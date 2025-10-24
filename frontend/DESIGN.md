# Frontend Design System

## Overview
Modern, dark-themed UI with glassmorphism effects, smooth animations, and a focus on quantum/scientific aesthetics.

## Design Features

### 🎨 Color Palette
- **Background**: Deep space navy (`#0a0e27`)
- **Primary Accent**: Purple-blue gradient (`#667eea` → `#a78bfa` → `#ec4899`)
- **Glass Effects**: Semi-transparent white overlays with backdrop blur
- **Text**: White with varying opacity for hierarchy

### ✨ Key Visual Elements

#### 1. **Animated Background**
- Radial gradient circles that slowly move
- Creates depth and movement
- Subtle purple/blue glow effects

#### 2. **Glassmorphism Cards**
- Semi-transparent backgrounds (`rgba(255, 255, 255, 0.03)`)
- Backdrop blur for depth
- Subtle borders and shadows

#### 3. **Element Cards**
- Hover effects with elevation
- Shine animation on hover
- Pulsing animation when selected
- Atomic number badge in corner
- Color-coded borders (blue default, pink when selected)

#### 4. **Buttons**
- Gradient backgrounds
- Shimmer effect on hover
- Smooth scale and elevation animations
- Disabled state with reduced opacity

#### 5. **Results Display**
- Slide-in animation
- Sectioned quantum data and AI predictions
- Emoji icons for visual hierarchy
- Monospace font for data values
- Hover effects on data rows

### 🎭 Animations

1. **Title Glow**: Brightness pulse (3s infinite)
2. **Background Move**: Gradient translation (20s infinite)
3. **Element Pulse**: Box-shadow pulse on selection (2s infinite)
4. **Button Shimmer**: Light sweep on hover
5. **Results Slide**: Entry animation from bottom
6. **Spinner**: Rotation animation during loading

### 🖼️ Typography

- **Primary Font**: Inter (modern, clean sans-serif)
- **Monospace**: JetBrains Mono (for data/code)
- **Weights**: 300 (light), 400 (regular), 600 (semi-bold), 800 (extra-bold)

### 📱 Responsive Design

- Flexible grid for periodic table
- Font size adjustments for mobile
- Padding reduction on small screens
- Touch-friendly button sizes

## Component Breakdown

### Header
```
- Large gradient title (3.5rem)
- Subtitle with reduced opacity
- Badge showing technology stack
```

### Periodic Table
```
- Auto-fit grid layout
- 9 elements currently
- Easy to expand with more elements
- Hover/selection states
```

### Results Panel
```
Two sections:
1. Quantum Data (⚛️)
   - Energy values
   - Electron counts
   - Orbital information

2. AI Prediction (🤖)
   - Products
   - Mechanism
   - Confidence score
   - Reasoning
```

### Loading State
```
- Large spinner (70px)
- Descriptive text
- Centered layout
```

## Usage

Simply open `index.html` in a modern browser. The design uses:
- CSS Grid
- Flexbox
- CSS custom properties
- Transform animations
- Backdrop filters

All styles are inline for easy deployment - no build process required!

## Browser Support

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (with vendor prefixes for backdrop-filter)

## Future Enhancements

- [ ] 3D molecule visualizations
- [ ] More element animations
- [ ] Dark/light mode toggle
- [ ] Export results as PDF
- [ ] Save/load reaction history
