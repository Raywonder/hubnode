const express = require('express');
const app = express();
const PORT = process.env.PORT || 3001;

app.use(express.json());
app.use('/api', require('./routes/index'));

app.listen(PORT, () => console.log(`Backend running on port ${PORT}`));
