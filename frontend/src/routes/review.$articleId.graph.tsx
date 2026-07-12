import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/review/$articleId/graph")({
  beforeLoad: ({ params }) => {
    throw redirect({ to: "/review/$articleId", params });
  },
  component: () => null,
});
