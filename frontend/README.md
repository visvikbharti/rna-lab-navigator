# RNA Lab Navigator - Frontend

Modern React frontend for the RNA Lab Navigator, providing an intuitive interface for RNA biology research queries.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your API endpoint

# Start development server
npm run dev

# Build for production
npm run build
```

## 📁 Directory Structure

```
frontend/
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── ChatInterface.jsx    # Main chat interface
│   │   ├── SearchBox.jsx        # Search functionality
│   │   └── enhanced/            # Enhanced UI components
│   ├── api/              # API client modules
│   ├── hooks/            # Custom React hooks
│   ├── contexts/         # React contexts
│   ├── pages/            # Page components
│   └── styles/           # CSS and style files
├── public/               # Static assets
└── vite.config.js       # Vite configuration
```

## 🎨 Key Features

- **Modern Chat Interface**: Real-time chat with the RAG system
- **Intelligent Suggestions**: Context-aware follow-up questions
- **Dark Mode**: Toggle between light and dark themes
- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: WebSocket support for live features

## 🛠️ Core Components

### 1. Chat Interface (`components/ChatInterface.jsx`)
- Message history with citations
- Typing indicators
- Suggestion chips
- Copy/export functionality

### 2. Search Components
- Advanced filters
- Real-time search
- Result highlighting
- Export capabilities

### 3. Enhanced UI (`components/enhanced/`)
- Glass morphism effects
- Smooth animations
- Floating particles
- Gradient text effects

## 🎯 UI/UX Guidelines

- **Colors**: Blue (#3B82F6) as primary, with gradient accents
- **Typography**: Inter font family
- **Spacing**: 8px grid system
- **Animations**: Subtle, <300ms transitions
- **Accessibility**: WCAG 2.1 AA compliant

## 🧪 Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

## 🔧 Development Tools

- **Vite**: Fast build tool
- **React 18**: Latest React features
- **Tailwind CSS**: Utility-first CSS
- **React Query**: Data fetching
- **Framer Motion**: Animations

## 📱 Responsive Breakpoints

- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

## 🚀 Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Analyze bundle size
npm run analyze
```

## 🌐 Deployment

The frontend is configured for deployment on Vercel. See `vercel.json` for configuration.

```bash
# Deploy to Vercel
vercel --prod
```

## 🔐 Security

- Content Security Policy headers
- XSS protection
- API key handling via environment variables
- HTTPS enforced in production

## 📊 Performance

- Lazy loading for routes
- Code splitting
- Image optimization
- < 3s initial load time target

## 🎨 Theming

The application supports custom themes. Edit `src/styles/design-tokens.css` to customize:
- Primary colors
- Font sizes
- Spacing
- Border radius
- Shadows

## 🤝 Contributing

1. Follow the existing component patterns
2. Use TypeScript for new components
3. Write tests for new features
4. Ensure accessibility compliance

## 📞 Support

For UI/UX issues or feature requests, contact the development team.# Deployment trigger Mon Jul  7 02:00:54 IST 2025
