module.exports = {
  host: process.env.D3VSKYMAN_HOST || '127.0.0.1',
  port: Number(process.env.D3VSKYMAN_PORT || 25120),
  password: process.env.D3VSKYMAN_PASSWORD || 'change-me',
  iv: process.env.D3VSKYMAN_IV || '0123456789abcdef',
  key: process.env.D3VSKYMAN_KEY || '0123456789abcdef0123456789abcdef'
};
