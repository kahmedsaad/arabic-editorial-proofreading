import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/lexical")({
  beforeLoad: () => {
    throw redirect({ to: "/" });
  },
  component: () => null,
});
