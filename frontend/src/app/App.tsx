import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";
import { router } from "./router";

// Server state via TanStack Query (ARCHITECTURE.md §3). One retry so a stub/501
// during the build doesn't spin; reads stay fresh for 30s. Offline mutation
// replay is deferred (TASKS.md); reads degrade to graceful states.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} future={{ v7_startTransition: true }} />
    </QueryClientProvider>
  );
}
