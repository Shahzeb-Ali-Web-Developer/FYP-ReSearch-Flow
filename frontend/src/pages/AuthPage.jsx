import React, { useState, useEffect } from 'react';
import { FaGoogle, FaFacebookF, FaApple, FaGithub, FaEye, FaEyeSlash } from 'react-icons/fa';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import researchLogo from '../assets/researchLogo.jpg'

const AuthPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { signIn, signUp, signInWithProvider, loading: authLoading } = useAuth();
  
  const [isLogin, setIsLogin] = useState(searchParams.get('mode') === 'login');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: ''
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // Update mode based on URL parameter
  useEffect(() => {
    const mode = searchParams.get('mode');
    setIsLogin(mode === 'login');
  }, [searchParams]);

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password) => {
    return password.length >= 8;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (!validatePassword(formData.password)) {
      newErrors.password = 'Password must be at least 8 characters long';
    }

    if (!isLogin) {
      if (!formData.fullName.trim()) {
        newErrors.fullName = 'Full name is required';
      }

      if (!formData.confirmPassword) {
        newErrors.confirmPassword = 'Please confirm your password';
      } else if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setErrors({});
    setSuccessMessage('');

    try {
      if (isLogin) {
        // Handle sign in
        const { error } = await signIn(formData.email, formData.password);
        
        if (error) {
          setErrors({ submit: error });
        } else {
          navigate('/'); // Redirect to dashboard or home page
        }
      } else {
        // Handle sign up
        const { error } = await signUp(
          formData.email, 
          formData.password, 
          { full_name: formData.fullName }
        );
        
        if (error) {
          setErrors({ submit: error });
        } else {
          setSuccessMessage('Account created successfully! Please check your email to verify your account.');
          setFormData({ email: '', password: '', confirmPassword: '', fullName: '' });
        }
      }
    } catch (error) {
      setErrors({ submit: 'An unexpected error occurred. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSocialLogin = async (provider) => {
    try {
      const { error } = await signInWithProvider(provider.toLowerCase());
      if (error) {
        setErrors({ submit: `Failed to sign in with ${provider}. Please try again.` });
      }
    } catch (error) {
      setErrors({ submit: `Failed to sign in with ${provider}. Please try again.` });
    }
  };

  const toggleAuthMode = () => {
    setIsLogin(!isLogin);
    setFormData({ email: '', password: '', confirmPassword: '', fullName: '' });
    setErrors({});
    setSuccessMessage('');
    
    // Update URL
    const newMode = !isLogin ? 'login' : 'signup';
    navigate(`/auth?mode=${newMode}`, { replace: true });
  };

  return (
    <div className="min-h-screen bg-[#391153] viga-font flex items-center justify-center p-4">
      <div className="w-full my-10 max-w-md">
        {/* Logo and Title */}
        <div className="text-center justify-center gap-2 flex flex-row">
          <div>
            <img className='h-12 w-12 rounded-xl' src={researchLogo} />
          </div>
          <div className="text-white">
            <h1 className="text-lg font-semibold">ReSearch Flow</h1>
            <p className="text-sm text-purple-200">AI Research Assistant</p>
          </div>
        </div>

        {/* Main Form Card */}
        <div className=" rounded-2xl p-8 ">
          <h2 className="text-2xl  text-white text-center mb-2">
            {isLogin ? 'Login' : 'Create Account'}
          </h2>
          
          <p className="text-purple-200 text-xs text-center mb-6">
            By {isLogin ? 'signing in' : 'creating an account'} you agree to accept our{' '}
            <span className="text-white underline cursor-pointer">Terms of Service</span> and{' '}
            <span className="text-white underline cursor-pointer">Privacy Policy</span>
          </p>

          {/* Success Message */}
          {successMessage && (
            <div className="mb-4 p-3 bg-green-500/20 border border-green-500/30 rounded-lg">
              <p className="text-green-200 text-sm text-center">{successMessage}</p>
            </div>
          )}

          {/* Error Message */}
          {errors.submit && (
            <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
              <p className="text-red-200 text-sm text-center">{errors.submit}</p>
            </div>
          )}

          {/* Social Login Buttons */}
          <div className="flex justify-center space-x-6 mb-2">
            {/* Google */}
            <button
              onClick={() => handleSocialLogin("Google")}
              disabled={isLoading || authLoading}
              className="w-14 h-14 flex items-center justify-center 
                         bg-transparent transition-all disabled:opacity-50 
                        animate-bounce delay-100"
            >
              <FaGoogle className=" text-red-800 text-3xl" />
            </button>

            {/* Github */}
            <button
              onClick={() => handleSocialLogin("Github")}
              disabled={isLoading || authLoading}
              className="w-14 h-14 flex items-center justify-center 
                         bg-transparent transition-all disabled:opacity-50 
                        animate-bounce delay-100"
            >
              <FaGithub className= "text-4xl" />
            </button>
          </div>


          <div className="relative mb-2">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-purple-500/30"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-purple-800/30 text-purple-200">Or continue with</span>
            </div>
          </div>

          {/* Form */}
          <div className="space-y-4">
            {/* Full Name Field (only for sign up) */}
            {!isLogin && (
              <div>
                <label className="block text-white text-sm font-medium mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleInputChange}
                  placeholder="Enter your full name"
                  className={`w-full px-4 py-3 bg-white/10 backdrop-blur-md border rounded-lg text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors ${
                    errors.fullName ? 'border-red-500' : 'border-purple-600/30'
                  }`}
                />
                {errors.fullName && (
                  <p className="mt-1 text-red-400 text-sm">{errors.fullName}</p>
                )}
              </div>
            )}

            {/* Email Field */}
            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Email"
                className={`w-full px-4 py-3 bg-white/10 backdrop-blur-md border rounded-lg text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors ${
                  errors.email ? 'border-red-500' : 'border-purple-600/30'
                }`}
              />
              {errors.email && (
                <p className="mt-1 text-red-400 text-sm">{errors.email}</p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder="Password"
                  className={`w-full px-4 py-3 pr-12 bg-white/10 backdrop-blur-md border rounded-lg text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors ${
                    errors.password ? 'border-red-500' : 'border-gray-600/30'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-purple-300 hover:text-white transition-colors"
                >
                  {showPassword ? <FaEyeSlash /> : <FaEye />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-red-400 text-sm">{errors.password}</p>
              )}
            </div>

            {/* Confirm Password Field (only for sign up) */}
            {!isLogin && (
              <div>
                <label className="block text-white text-sm font-medium mb-2">
                  Re-Password*
                </label>
                <div className="relative">
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    placeholder="Re-Password"
                    className={`w-full px-4 py-3 pr-12 bg-white/10 backdrop-blur-md border rounded-lg text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors ${
                      errors.confirmPassword ? 'border-red-500' : 'border-purple-600/30'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-purple-300 hover:text-white transition-colors"
                  >
                    {showConfirmPassword ? <FaEyeSlash /> : <FaEye />}
                  </button>
                </div>
                {errors.confirmPassword && (
                  <p className="mt-1 text-red-400 text-sm">{errors.confirmPassword}</p>
                )}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isLoading || authLoading}
              className="w-full bg-purple-700 hover:bg-purple-900 disabled:bg-purple-800 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-purple-800"
            >
              {isLoading || authLoading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  {isLogin ? 'Signing in...' : 'Creating account...'}
                </div>
              ) : (
                isLogin ? 'Sign in' : 'Sign up'
              )}
            </button>
          </div>

          {/* Toggle Auth Mode */}
          <div className="mt-6 text-center">
            <span className="text-purple-200 text-sm">
              {isLogin ? "Don't have an account?" : "Already have an account?"}{' '}
              <button
                onClick={toggleAuthMode}
                disabled={isLoading || authLoading}
                className="text-white font-semibold hover:underline focus:outline-none disabled:opacity-50"
              >
                {isLogin ? 'Sign up' : 'Log in'}
              </button>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;