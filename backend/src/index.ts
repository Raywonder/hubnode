import express from 'express';
import dotenv from 'dotenv';
import authRoutes from './routes/auth.route';
import userRoutes from './routes/user.route';
import appRoutes from './routes/app.route';
import statusRoutes from "./routes/status.route";

dotenv.config();

const app = express();
const port = process.env.PORT || 3001;

app.use(express.json());

// Register routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/app', appRoutes);
app.use('/api/status', statusRoutes);

app.listen(port, () => {
  console.log(`?? Backend API running on http://localhost:${port}`);
});
