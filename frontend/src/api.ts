import axios from "axios";
export const api = axios.create({ baseURL: "/api", withCredentials: true });
export type Row = Record<string, any>;
export function message(e: unknown): string {
  return axios.isAxiosError(e)
    ? typeof e.response?.data?.detail === "string"
      ? e.response.data.detail
      : JSON.stringify(e.response?.data?.detail) || e.message
    : String(e);
}
