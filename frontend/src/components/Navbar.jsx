import React, { useState, useEffect, useRef } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import researchLogo from "../assets/researchLogo.jpg";
import { Menu, User, LogOut, Settings } from "lucide-react";
import { useAuth } from "../contexts/AuthContext.jsx";

export default function Navbar() {
  const [visible, setVisible] = useState(false);
  const [userMenuVisible, setUserMenuVisible] = useState(false);
  const { user, isAuthenticated, signOut, loading } = useAuth();

  const menuRef = useRef(null);
  const buttonRef = useRef(null);
  const userMenuRef = useRef(null);
  const userButtonRef = useRef(null);
  const navigate = useNavigate();

  // Handle clicks outside menus
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target)
      ) {
        setVisible(false);
      }
      if (
        userMenuRef.current &&
        !userMenuRef.current.contains(event.target) &&
        userButtonRef.current &&
        !userButtonRef.current.contains(event.target)
      ) {
        setUserMenuVisible(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogin = () => navigate("/auth?mode=login");
  const handleSignUp = () => navigate("/auth?mode=signup");

  const handleLogout = async () => {
    try {
      await signOut();
      setUserMenuVisible(false);
      navigate("/");
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  const handleProfile = () => {
    navigate("/profile");
    setUserMenuVisible(false);
  };

  const handleSettings = () => {
    navigate("/settings");
    setUserMenuVisible(false);
  };

  const getUserInitials = (user) => {
    if (!user) return "U";
    const name = user.user_metadata?.full_name || user.email;
    if (name) {
      return name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2);
    }
    return "U";
  };

  const getUserDisplayName = (user) => {
    if (!user) return "User";
    return (
      user.user_metadata?.full_name ||
      user.email?.split("@")[0] ||
      "User"
    );
  };

  const NavButton = ({ children, primary = false, onClick }) => (
    <button
      onClick={onClick}
      className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors border ${
        primary
          ? "bg-black text-white border-black hover:bg-gray-800"
          : "text-gray-700 border-transparent hover:border-gray-300 hover:bg-gray-100"
      }`}
    >
      {children}
    </button>
  );

  const UserAvatar = ({ user, onClick }) => (
    <button
      ref={userButtonRef}
      onClick={onClick}
      className="flex items-center space-x-2 px-3 py-2 rounded-full bg-white/10 hover:bg-white/20 transition-all duration-200 border border-white/20"
    >
      <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
        {user?.user_metadata?.avatar_url ? (
          <img
            src={user.user_metadata.avatar_url}
            alt={getUserDisplayName(user)}
            className="w-8 h-8 rounded-full object-cover"
          />
        ) : (
          getUserInitials(user)
        )}
      </div>
      <span className="text-white text-sm font-medium hidden sm:block">
        {getUserDisplayName(user)}
      </span>
    </button>
  );

  const UserMenu = () => (
    <div
      ref={userMenuRef}
      className="absolute right-0 mt-2 w-48 py-2 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
    >
      <div className="px-4 py-2 border-b border-gray-100">
        <p className="text-sm font-medium text-gray-900">
          {getUserDisplayName(user)}
        </p>
        <p className="text-sm text-gray-500">{user?.email}</p>
      </div>

      <button
        onClick={handleProfile}
        className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
      >
        <User className="w-4 h-4" />
        <span>Profile</span>
      </button>

      <button
        onClick={handleSettings}
        className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
      >
        <Settings className="w-4 h-4" />
        <span>Settings</span>
      </button>

      <hr className="my-1" />

      <button
        onClick={handleLogout}
        className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center space-x-2"
      >
        <LogOut className="w-4 h-4" />
        <span>Sign out</span>
      </button>
    </div>
  );

  if (loading) {
    return (
      <header className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 flex items-center justify-center">
              <img className="rounded-lg" src={researchLogo} alt="ReSearch Flow" />
            </div>
            <div className="hidden md:block">
              <h1 className="text-lg font-semibold text-black">ReSearch Flow</h1>
              <p className="text-xs text-gray-500">AI Research Assistant</p>
            </div>
          </div>
          <div className="w-20 h-6 bg-gray-200 rounded-full animate-pulse"></div>
        </div>
      </header>
    );
  }

  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 flex items-center justify-center">
          <img className="rounded-lg" src={researchLogo} alt="ReSearch Flow" />
        </div>
        <div className="hidden md:block">
          <h1 className="text-lg font-semibold text-black">ReSearch Flow</h1>
          <p className="text-xs text-gray-500">AI Research Assistant</p>
        </div>
      </div>

      <nav className="hidden md:flex items-center space-x-2 text-sm">
        <NavButton>About</NavButton>
        <NavButton>Features</NavButton>
        <NavButton>Contact</NavButton>
      </nav>

      <div className="hidden md:flex items-center space-x-2">
        {isAuthenticated ? (
          <div className="relative">
            <UserAvatar
              user={user}
              onClick={() => setUserMenuVisible(!userMenuVisible)}
            />
            {userMenuVisible && <UserMenu />}
          </div>
        ) : (
          <>
            <button
              onClick={handleLogin}
              className="text-sm text-gray-700 hover:text-black"
            >
              Log in
            </button>
            <NavButton primary onClick={handleSignUp}>Sign up</NavButton>
          </>
        )}
      </div>

      <div className="relative md:hidden">
        <button
          ref={buttonRef}
          onClick={() => setVisible(!visible)}
          className="z-20 p-2 bg-white rounded-full border border-gray-300"
        >
          <Menu className="w-4 h-4 text-gray-700" />
        </button>

        {visible && (
          <div
            ref={menuRef}
            className="absolute right-0 mt-2 w-40 py-3 px-5 bg-white text-gray-700 rounded shadow-md border border-gray-200 flex flex-col gap-2 z-50"
          >
            <NavLink to="/About" onClick={() => setVisible(false)}>
              About
            </NavLink>
            <NavLink to="/Features" onClick={() => setVisible(false)}>
              Features
            </NavLink>
            <NavLink to="/Contact" onClick={() => setVisible(false)}>
              Contact
            </NavLink>

            {!isAuthenticated && (
              <div>
                <hr className="my-2" />
                <button
                  onClick={() => {
                    handleLogin();
                    setVisible(false);
                  }}
                  className="text-left text-gray-700 hover:text-black"
                >
                  Log in
                </button>
                <button
                  onClick={() => {
                    handleSignUp();
                    setVisible(false);
                  }}
                  className="mt-1 text-left text-black font-medium"
                >
                  Sign up
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
    </header>
  );
}
