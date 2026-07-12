import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/review/$articleId/semantic")({
  beforeLoad: ({ params }) => {
    throw redirect({ to: "/review/$articleId", params });
  },
  component: () => null,
});
