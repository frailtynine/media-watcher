// Login example
import { useState } from 'react';
import { authApi } from '../api';
import { Field, Input, Box, Button } from '@chakra-ui/react';
import { useComponent } from '../hooks/Сomponent';
import Dashboard from '../Pages/Dashboard';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { setCurrentComponent } = useComponent();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    const success = await authApi.login({ 
      username: email, 
      password 
    });
    
    if (success) {
      setCurrentComponent(<Dashboard />);
    } else {
      setError('Invalid credentials');
    }
  };

  return (
    <Box>
      <Field.Root invalid={!!error}>
        <Field.Label>Email</Field.Label>
          <Input 
            type="email" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            required
            id='email-input'
          />
        <Field.Label>Password</Field.Label>
          <Input 
            type="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            required
            id='password-input'
          />
        <Field.ErrorText>{error}</Field.ErrorText>
      </Field.Root>
      <Button onClick={handleLogin}>
        Login
      </Button>
    </Box>
  );
}