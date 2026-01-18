import { clerkMiddleware } from '@clerk/nextjs/server';

export default clerkMiddleware({
  // Add any Clerk middleware options here if needed
});

// Match all routes in the app so auth() is available in Server Components
export const config = {
  matcher: '/((?!_next/static|_next/image|favicon.ico).*)',
};
