import axios from "axios";

export const api = axios.create({
  baseURL: "/api/v1",
  withCredentials: true, // For cookies if needed, but we are using Authorization headers
});

api.interceptors.request.use((config) => {
  // In Next.js App Router, we'll often pass the token explicitly in Server Components.
  // For client components, we can get it from localStorage or a global store.
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("dashboard_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});
