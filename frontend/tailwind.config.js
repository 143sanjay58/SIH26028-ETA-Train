/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#0c0e14',
          50: '#0c0e14',
          100: '#111318',
          200: '#161820',
          300: '#1c1f28',
          400: '#232730',
          500: '#2c3040',
          600: '#3a3f52',
          700: '#4a5068',
          800: '#6b7280',
          900: '#9ca3af',
        },
        accent: {
          DEFAULT: '#00d4ff',
          50: '#e6fbff',
          100: '#b3f3ff',
          200: '#80ebff',
          300: '#4de3ff',
          400: '#1adbff',
          500: '#00d4ff',
          600: '#00aacc',
          700: '#008099',
          800: '#005566',
          900: '#002b33',
        },
        violet: {
          DEFAULT: '#8b5cf6',
          50: '#f3f0ff',
          100: '#e0d8ff',
          200: '#c4b5fd',
          300: '#a78bfa',
          400: '#8b5cf6',
          500: '#7c3aed',
          600: '#6d28d9',
          700: '#5b21b6',
          800: '#4c1d95',
          900: '#3b0764',
        },
        rail: {
          green: '#10b981',
          amber: '#f59e0b',
          red: '#ef4444',
          blue: '#3b82f6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'display-xl': ['3.5rem', { lineHeight: '1.1', fontWeight: '700', letterSpacing: '-0.02em' }],
        'display-lg': ['2.5rem', { lineHeight: '1.15', fontWeight: '700', letterSpacing: '-0.02em' }],
        'display-md': ['2rem', { lineHeight: '1.2', fontWeight: '600', letterSpacing: '-0.01em' }],
        'display-sm': ['1.5rem', { lineHeight: '1.3', fontWeight: '600' }],
      },
      boxShadow: {
        'glow-sm': '0 0 15px -3px rgba(0, 212, 255, 0.15)',
        'glow': '0 0 30px -5px rgba(0, 212, 255, 0.2)',
        'glow-lg': '0 0 60px -10px rgba(0, 212, 255, 0.3)',
        'glow-violet': '0 0 30px -5px rgba(139, 92, 246, 0.2)',
        'glow-red': '0 0 30px -5px rgba(239, 68, 68, 0.3)',
        'glow-green': '0 0 20px -5px rgba(16, 185, 129, 0.3)',
        'inner-glow': 'inset 0 1px 0 0 rgba(255, 255, 255, 0.05)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
        'slide-in': 'slide-in 0.3s ease-out',
        'slide-up': 'slide-up 0.3s ease-out',
        'fade-in': 'fade-in 0.3s ease-out',
        'counter': 'counter 1s ease-out',
        'scan-line': 'scan-line 3s linear infinite',
        'data-stream': 'data-stream 2s linear infinite',
      },
      keyframes: {
        'glow-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
        'slide-in': {
          '0%': { transform: 'translateX(-10px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'scan-line': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        'data-stream': {
          '0%': { backgroundPosition: '0% 0%' },
          '100%': { backgroundPosition: '100% 100%' },
        },
      },
      backgroundImage: {
        'grid-pattern': 'linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px)',
        'radial-glow': 'radial-gradient(circle at center, rgba(0, 212, 255, 0.08) 0%, transparent 70%)',
      },
      backgroundSize: {
        'grid': '40px 40px',
      },
      borderWidth: {
        '1': '1px',
      },
    },
  },
  plugins: [],
}
