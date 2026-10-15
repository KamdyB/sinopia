// First-party API proxy for the Vercel-hosted coach app.
// Configure SINOPIA_BACKEND_URL in the Vercel project environment.
// Browser cookies remain first-party because the browser only talks to this origin.
declare const process: { env: Record<string, string | undefined> };

export const config = { runtime: "edge" };

const ALLOWED_METHODS = new Set(["GET", "POST", "DELETE", "OPTIONS"]);

export default async function handler(request: Request): Promise<Response> {
  if (!ALLOWED_METHODS.has(request.method)) {
    return new Response("Method not allowed.", {
      status: 405,
      headers: { Allow: "GET, POST, DELETE, OPTIONS", "Cache-Control": "no-store" },
    });
  }

  const backend = process.env.SINOPIA_BACKEND_URL?.trim().replace(/\/+$/, "");
  if (!backend) {
    return new Response("The API service is not configured.", {
      status: 503,
      headers: { "Cache-Control": "no-store", "Content-Type": "text/plain; charset=utf-8" },
    });
  }

  const incoming = new URL(request.url);
  if (!incoming.pathname.startsWith("/api/")) {
    return new Response("Not found.", {
      status: 404,
      headers: { "Cache-Control": "no-store" },
    });
  }

  const backendPath = incoming.pathname.slice("/api".length);
  const target = backend + backendPath + incoming.search;
  const headers = new Headers(request.headers);
  for (const name of [
    "host", "content-length", "connection", "accept-encoding",
    "x-forwarded-for", "x-real-ip", "x-forwarded-host",
    "x-sinopia-proxy-secret", "x-sinopia-client-ip",
  ]) headers.delete(name);

  const proxySecret = process.env.SINOPIA_PROXY_SECRET?.trim();
  if (!proxySecret || proxySecret.length < 32) {
    return new Response("The API proxy is not configured.", {
      status: 503,
      headers: { "Cache-Control": "no-store", "Content-Type": "text/plain; charset=utf-8" },
    });
  }
  headers.set("X-Sinopia-Proxy-Secret", proxySecret);
  const forwarded = request.headers.get("x-forwarded-for") || "";
  const forwardedParts = forwarded.split(",").map((part) => part.trim()).filter(Boolean);
  const clientIp = forwardedParts[forwardedParts.length - 1];
  if (clientIp && clientIp.length <= 64) headers.set("X-Sinopia-Client-IP", clientIp);

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers,
      body: request.method === "GET" || request.method === "OPTIONS"
        ? undefined
        : await request.arrayBuffer(),
      redirect: "manual",
      cache: "no-store",
    });
  } catch {
    return new Response("The API service is temporarily unavailable.", {
      status: 502,
      headers: { "Cache-Control": "no-store", "Content-Type": "text/plain; charset=utf-8" },
    });
  }

  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.set("Cache-Control", "no-store");
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");
  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}
