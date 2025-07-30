import { Request, Response } from 'express';

export const getUser = (req: Request, res: Response) => {
  const userId = req.params.id;
  // Placeholder response
  return res.json({ id: userId, name: 'Sample User' });
};
