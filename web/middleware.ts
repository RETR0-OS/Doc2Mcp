import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

const isPublicRoute = createRouteMatcher(['/', '/api/(.*)']);
const isDashboardRoute = createRouteMatcher(['/dashboard(.*)']);

export default clerkMiddleware(async (auth, req) => {
  const { userId } = await auth();
  
  // If user is signed in and on the home page, redirect to dashboard
  if (userId && req.nextUrl.pathname === '/') {
    return NextResponse.redirect(new URL('/dashboard', req.url));
  }
  
  // If user is not signed in and trying to access dashboard, redirect to home
  if (!userId && isDashboardRoute(req)) {
    return NextResponse.redirect(new URL('/', req.url));
  }
});

// Match all routes except static files
export const config = {
  matcher: '/((?!_next/static|_next/image|favicon.ico).*)',
};
