/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0B0B12',
        surface: '#151522',
        'surface-2': '#1C1C2E',
        border: '#252540',
        'purple-primary': '#7C3AED',
        'purple-secondary': '#A855F7',
        'purple-glow': '#6D28D9',
        'text-primary': '#E5E7EB',
        'text-muted': '#6B7280',
        'text-dim': '#4B5563',
        green: '#10B981',
        red: '#EF4444',
        yellow: '#F59E0B',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.4), 0 0 0 1px rgba(37,37,64,0.6)',
        'purple-glow': '0 0 20px rgba(124,58,237,0.25)',
        'purple-glow-sm': '0 0 10px rgba(124,58,237,0.15)',
      },
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'blink': 'blink 1.2s step-end infinite',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0 },
        },
      },
    },
  },
  plugins: [],
}
