import { Router } from 'express';
import { getUser } from '../services/user.service';

const router = Router();

router.get('/:id', getUser);

export default router;
