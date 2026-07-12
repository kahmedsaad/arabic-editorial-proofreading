import { createFileRoute, redirect } from "@tanstack/react-router";

/** Internal know-how route — redirected away from public demo. */
export const Route = createFileRoute("/review/$articleId/phases")({
  beforeLoad: ({ params }) => {
    throw redirect({ to: "/review/$articleId", params });
  },
  component: () => null,
});
