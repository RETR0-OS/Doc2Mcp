import { authMiddleware } from "@clerk/nextjs/edge";

export default authMiddleware({
  publicRoutes: ["/", "/api/webhooks(.*)"],
});

export const config = {
  matcher: ["/((?!.+\\.[\\w]+$|_next).*)", "/", "/(api|trpc)(.*)"],
};
