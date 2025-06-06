import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.SUPABASE_JWT_SECRET || '';

if (!JWT_SECRET) {
  console.error('Missing SUPABASE_JWT_SECRET in environment variables');
  process.exit(1);
}

// Extend Express Request type to include user and properly typed body
export interface AuthenticatedRequest extends Request {
  user?: { id: string; email?: string };
  body: any; // This ensures body property is available with proper typing
}

export const authenticate = (req: Request, res: Response, next: NextFunction) => {
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing or invalid Authorization header' });
  }
  const token = authHeader.split(' ')[1];
  try {
    const payload = jwt.verify(token, JWT_SECRET) as { sub: string; email?: string };
    (req as AuthenticatedRequest).user = { id: payload.sub, email: payload.email };
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
}; 