import { Request, Response } from 'express';

export const login = (req: Request, res: Response) => {
  const { email, password } = req.body;
  // Placeholder logic
  return res.json({ token: 'fake-jwt-token', email });
};

export const register = (req: Request, res: Response) => {
  const { email, password } = req.body;
  // Placeholder logic
  return res.status(201).json({ message: 'User registered', email });
};
