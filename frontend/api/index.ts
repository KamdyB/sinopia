// First-party API proxy for the Vercel-hosted coach app.
// SINOPIA_BACKEND_URL overrides the production API origin when set.
// Browser cookies remain first-party because the browser only talks to this origin.
declare const process: { env: Record<string, string | undefined> };

export const config = { runtime: "edge" };

const DEFAULT_BACKEND_ORIGIN = "https://sinopia-api.vercel.app";
const ALLOWED_METHODS = new Set(["GET", "POST", "DELETE", "OPTIONS"]);

export default async function handler(request: Request): Promise<Response> {
  if (!ALLOWED_METHODS.has(request.method)) {
    return new Response("Method not allowed.", {
      status: 405,
      headers: { Allow: "GET, POST, DELETE, OPTIONS", "Cache-Control": "no-store" },
    });
  }

  const configuredBackend = process.env.SINOPIA_BACKEND_URL?.trim();
  const backend = (configuredBackend || DEFAULT_BACKEND_ORIGIN).replace(/\/+$/, "");
  let backendUrl: URL;
  try {
    backendUrl = new URL(backend);
  } catch {
    return new Response("The API service URL is invalid.", {
      status: 503,
      headers: { "Cache-Control": "no-store", "Content-Type": "text/plain; charset=utf-8" },
    });
  }
  if (backendUrl.protocol !== "https:" || backendUrl.pathname !== "/" || backendUrl.search || backendUrl.hash || backendUrl.username || backendUrl.password) {
    return new Response("The API service URL must be an HTTPS origin without a path.", {
      status: 503,
      headers: { "Cache-Control": "no-store", "Content-Type": "text/plain; charset=utf-8" },
    });
  }

  const incoming = new URL(request.url);
  const routedPath = incoming.searchParams.get("__sinopia_path") || "";
  if (!routedPath || routedPath.startsWith("/") || routedPath.includes("..")) {
    return new Response("Not found.", {
      status: 404,
      headers: { "Cache-Control": "no-store" },
    });
  }

  const forwardedQuery = new URLSearchParams(incoming.searchParams);
  forwardedQuery.delete("__sinopia_path");
  const queryString = forwardedQuery.toString();
  const backendPath = "/" + routedPath;
  const target = backendUrl.origin + backendPath + (queryString ? "?" + queryString : "");
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
