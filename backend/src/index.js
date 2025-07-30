const express = require('express');
const app = express();
require('dotenv').config();

const PORT = process.env.PORT || 3001;

app.get('/', (req, res) => {
  res.send('HubNode backend is running');
});

app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
