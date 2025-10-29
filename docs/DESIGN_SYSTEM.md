# F1 Racing Simulator - Design System Documentation

> Comprehensive design guide for creating a matching dashboard that follows the attract pages' look and feel

---

## Table of Contents

1. [Overview](#overview)
2. [Color Palette](#color-palette)
3. [Typography](#typography)
4. [Spacing & Layout](#spacing--layout)
5. [Components](#components)
6. [Animations](#animations)
7. [Brand Assets](#brand-assets)
8. [Implementation Guide](#implementation-guide)

---

## Overview

The F1 Racing Simulator uses a **Salesforce-inspired design system** with F1 partnership branding. The visual language combines professional enterprise aesthetics with the energy and excitement of Formula 1 racing.

### Design Principles
- **Professional yet Energetic**: Balances corporate polish with racing excitement
- **High Contrast**: Bold colors with strong readability
- **Motion & Animation**: Smooth, purposeful animations enhance the experience
- **Responsive**: Adapts gracefully from mobile to ultra-wide displays (5120×1440px)
- **Accessible**: Strong color contrast, clear typography, readable at distance

---

## Color Palette

### Primary Colors

```css
:root {
  /* Brand Blues - Primary */
  --deep-blue: #032D60;           /* Dark navy - headers, text, primary elements */
  --bright-blue: #00529F;         /* Medium blue - main backgrounds, buttons */
  --cloud-blue: #00A1E0;          /* Light sky blue - accents, gradients */

  /* Accent */
  --gold-yellow: #FFB740;         /* Gold - highlights, CTAs, important elements */

  /* Neutrals */
  --white: #FFFFFF;               /* Cards, text on dark backgrounds */
  --dark-gray: #3E3E3C;           /* Body text, icons */
  --light-gray: #54698D;          /* Secondary text, subtle elements */
  --light-blue-bg: #F3F6F9;       /* Light backgrounds, QR containers */
}
```

### State Colors

```css
--success-green: #2E844A;        /* Connected status, positive actions */
--warning-yellow: #FFB740;       /* Warnings, attention needed */
--error-red: #C23934;            /* Errors, disconnected states */
```

### Usage Guidelines

| Element Type | Primary Color | Secondary Color | Text Color |
|--------------|---------------|-----------------|------------|
| Page Background | `bright-blue` gradient | `deep-blue` | `white` |
| Card Background | `white` | `light-blue-bg` | `dark-gray` |
| Primary Button | `gold-yellow` gradient | `cloud-blue` | `deep-blue` |
| Secondary Button | `bright-blue` | - | `white` |
| Headers | `deep-blue` | - | - |
| Body Text | `dark-gray` | `light-gray` | - |
| Links/Interactive | `bright-blue` | `cloud-blue` (hover) | - |

### Gradient Patterns

```css
/* Background Gradient */
background: radial-gradient(circle at top, var(--bright-blue) 0%, var(--deep-blue) 100%);

/* Accent Gradient */
background: linear-gradient(135deg, var(--gold-yellow) 0%, var(--cloud-blue) 100%);

/* Success Gradient */
background: linear-gradient(135deg, var(--success-green) 0%, var(--gold-yellow) 100%);
```

---

## Typography

### Font Stack

**Primary**: System fonts with Inter fallback for web performance
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto',
             'Helvetica Neue', sans-serif;
```

**Headlines**: Verdana for maximum compatibility and readability
```css
font-family: 'Verdana', 'Geneva', sans-serif;
```

**Monospace**: For times, scores, technical data
```css
font-family: 'Courier New', monospace;
```

### Type Scale

| Style | Size | Weight | Line Height | Letter Spacing | Use Case |
|-------|------|--------|-------------|----------------|----------|
| **Display** | 54px | 900 | 1.1 | -1px | Main page titles |
| **H1** | 36px | 700 | 1.2 | 0 | Section headers |
| **H2** | 24px | 600 | 1.3 | 0 | Card headers |
| **H3** | 20px | 600 | 1.4 | 0 | Subheaders |
| **Body Large** | 20px | 400 | 1.6 | 0 | Important body text |
| **Body** | 16px | 400 | 1.5 | 0 | Standard text |
| **Small** | 14px | 400 | 1.4 | 0 | Captions, labels |
| **Tiny** | 12px | 500 | 1.3 | 1px | Uppercase labels |

### Typography Examples

```css
/* Main Title */
.main-title {
  font-size: 54px;
  font-weight: 900;
  color: var(--white);
  letter-spacing: -1px;
  text-align: center;
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* Card Header */
.card-header {
  font-size: 24px;
  font-weight: 600;
  color: var(--deep-blue);
  margin-bottom: 16px;
}

/* Label (uppercase) */
.label {
  font-size: 12px;
  font-weight: 500;
  color: var(--light-gray);
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Body Text */
.body-text {
  font-size: 16px;
  font-weight: 400;
  color: var(--dark-gray);
  line-height: 1.5;
}
```

### Responsive Typography

```css
@media (max-width: 768px) {
  .main-title { font-size: 36px; }      /* 67% of desktop */
  .card-header { font-size: 20px; }     /* 83% of desktop */
  .body-text { font-size: 14px; }       /* 88% of desktop */
}
```

---

## Spacing & Layout

### Spacing Scale

Use consistent spacing values throughout the design:

```css
:root {
  --spacing-xs: 8px;      /* Tight spacing, icon gaps */
  --spacing-sm: 16px;     /* Default gaps between related elements */
  --spacing-md: 24px;     /* Card padding, section gaps */
  --spacing-lg: 32px;     /* Large section spacing */
  --spacing-xl: 48px;     /* Major section breaks */
  --spacing-2xl: 64px;    /* Page-level spacing */
}
```

### Border Radius

Rounded corners create a friendly, modern feel:

```css
:root {
  --radius-sm: 8px;       /* Small elements, badges */
  --radius-md: 12px;      /* Cards, buttons */
  --radius-lg: 16px;      /* Large cards */
  --radius-xl: 24px;      /* Special elements, pill shapes */
}
```

### Shadow System

Four-level shadow system for depth hierarchy:

```css
:root {
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);      /* Subtle elevation */
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.12);     /* Card default */
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.16);     /* Card hover */
  --shadow-xl: 0 12px 32px rgba(0, 0, 0, 0.2);     /* Modals, overlays */
}
```

### Layout Patterns

#### Fullscreen Container
```css
.fullscreen-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at top, var(--bright-blue) 0%, var(--deep-blue) 100%);
  overflow: hidden;
}
```

#### Card Component
```css
.card {
  background: var(--white);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}
```

#### Grid Layout (3-column)
```css
.grid-3col {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

@media (max-width: 768px) {
  .grid-3col {
    grid-template-columns: 1fr;
  }
}
```

---

## Components

### 1. Logo Circle

**Visual Design:**
- Circular container with gradient background
- Contains racing car emoji 🏎️
- Pulsing animation for attention

```css
.logo-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--gold-yellow), var(--cloud-blue));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 64px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  animation: pulse 2s infinite;
}

@media (max-width: 768px) {
  .logo-circle {
    width: 80px;
    height: 80px;
    font-size: 48px;
  }
}
```

### 2. Rig Badge

**Visual Design:**
- Pill-shaped badge
- White background
- Shows rig number prominently

```css
.rig-badge {
  background: var(--white);
  padding: 8px 24px;
  border-radius: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.rig-badge-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--light-gray);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.rig-badge-number {
  font-size: 24px;
  font-weight: 700;
  color: var(--bright-blue);
}
```

### 3. QR Code Card

**Visual Design:**
- White card with light blue background for QR code
- Centered QR code with instructions below
- Phone emoji for clarity

```css
.qr-card {
  background: var(--white);
  padding: 32px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  text-align: center;
  max-width: 450px;
}

.qr-container {
  background: var(--light-blue-bg);
  padding: 24px;
  border-radius: var(--radius-md);
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.qr-instructions {
  font-size: 18px;
  color: var(--dark-gray);
  margin-top: 16px;
}
```

**QR Code Settings:**
```javascript
// Using qrcode.react library
<QRCodeSVG
  value="https://your-url.com"
  size={280}
  fgColor="#032D60"        // deep-blue
  bgColor="#FFFFFF"        // white
  level="H"                // High error correction
/>
```

### 4. Step Circle

**Visual Design:**
- Circular numbered steps
- Gold background with deep blue text
- Used in call-to-action flows

```css
.step-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--gold-yellow);
  color: var(--deep-blue);
  font-size: 28px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(255, 183, 64, 0.4);
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .step-circle {
    width: 48px;
    height: 48px;
    font-size: 20px;
  }
}
```

### 5. Status Indicator

**Visual Design:**
- Colored dot with blinking animation
- Text label showing connection status
- Glowing effect for connected state

```css
.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--success-green);
  box-shadow: 0 0 12px rgba(46, 132, 74, 0.8);
  animation: blinkStatus 2s infinite;
}

.status-dot.disconnected {
  background: var(--error-red);
  box-shadow: 0 0 12px rgba(194, 57, 52, 0.8);
  animation: none;
}

.status-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--dark-gray);
}
```

### 6. Button Styles

**Primary Button:**
```css
.btn-primary {
  padding: 16px 32px;
  font-size: 18px;
  font-weight: 600;
  color: var(--deep-blue);
  background: linear-gradient(135deg, var(--gold-yellow), var(--cloud-blue));
  border: none;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.btn-primary:active {
  transform: translateY(0);
  box-shadow: var(--shadow-sm);
}
```

**Secondary Button:**
```css
.btn-secondary {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  color: var(--white);
  background: var(--bright-blue);
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: var(--cloud-blue);
  border-color: var(--white);
}
```

---

## Animations

### Keyframe Definitions

#### 1. Float Animation
**Use:** Clouds, decorative elements, icons
```css
@keyframes float {
  0%, 100% { transform: translateY(-10px); }
  50% { transform: translateY(-30px); }
}

.floating-element {
  animation: float 3s ease-in-out infinite;
}
```

#### 2. Pulse Animation
**Use:** Logo, important elements
```css
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.pulsing-element {
  animation: pulse 2s ease-in-out infinite;
}
```

#### 3. Slide In Animation
**Use:** Page entry, card entrance
```css
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slide-in {
  animation: slideIn 0.6s ease-out;
}
```

#### 4. Fade In Up
**Use:** Staggered content reveal
```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-up {
  animation: fadeInUp 0.5s ease-out;
  animation-fill-mode: both;
}

/* Staggered delays */
.fade-in-up:nth-child(1) { animation-delay: 0.1s; }
.fade-in-up:nth-child(2) { animation-delay: 0.2s; }
.fade-in-up:nth-child(3) { animation-delay: 0.3s; }
```

#### 5. Bounce Animation
**Use:** Arrows, indicators
```css
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.bouncing-arrow {
  animation: bounce 2s ease-in-out infinite;
}
```

#### 6. Rotate Animation
**Use:** Loading indicators, stars
```css
@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.rotating-icon {
  animation: rotate 4s linear infinite;
}
```

#### 7. Blink Status
**Use:** Status dots, connection indicators
```css
@keyframes blinkStatus {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.status-blink {
  animation: blinkStatus 2s ease-in-out infinite;
}
```

#### 8. Pulse Glow
**Use:** Success states, active elements
```css
@keyframes pulseGlow {
  0%, 100% {
    box-shadow: 0 0 8px rgba(46, 132, 74, 0.4);
  }
  50% {
    box-shadow: 0 0 20px rgba(46, 132, 74, 0.8);
  }
}

.glowing-element {
  animation: pulseGlow 2s ease-in-out infinite;
}
```

### Transition Standards

```css
:root {
  --transition-fast: 0.2s ease-in-out;      /* Micro-interactions */
  --transition-normal: 0.3s ease-in-out;    /* Standard hover/focus */
  --transition-slow: 0.5s ease-in-out;      /* Large movements */
}
```

### Animation Timing Guidelines

| Duration | Use Case |
|----------|----------|
| 0.2s | Button hover, color changes |
| 0.3s | Card hover, transform effects |
| 0.5-0.6s | Page transitions, slide-ins |
| 2s | Continuous pulse, status blink |
| 3s+ | Ambient animations (clouds, float) |

---

## Brand Assets

### 1. Official Logo

**File:** `SF_F1_logo.jpeg`

**Description:**
- Salesforce + F1 partnership logo
- Features: F1 Red logo + Salesforce Cloud mark
- Text: "Global Partner of Formula 1®"

**Usage:**
```html
<img src="/SF_F1_logo.jpeg" alt="Salesforce Formula 1 Partnership" />
```

**Styling:**
```css
.brand-logo {
  width: 200px;
  height: auto;
  object-fit: contain;
}
```

### 2. Background Video

**File:** `F1 25 Trailer 1080p.mp4`
**Duration:** 102 seconds
**Resolution:** 1920×1080

**Usage:** Background for ultra-wide simulator screens

```html
<video autoplay loop muted playsinline>
  <source src="/F1 25 Trailer 1080p.mp4" type="video/mp4">
</video>
```

**Styling:**
```css
.background-video {
  position: absolute;
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: brightness(0.6);  /* Dim for readability */
  z-index: 0;
}
```

### 3. Theme Audio

**File:** `f1_theme_brian_tyler.mp3`
**Description:** Official F1 theme music by Brian Tyler

**Usage:**
```html
<audio id="bgMusic" loop>
  <source src="/f1_theme_brian_tyler.mp3" type="audio/mpeg">
</audio>
```

### 4. Emoji Icons

Consistently used emoji for visual clarity:

| Emoji | Code | Use Case |
|-------|------|----------|
| 🏎️ | Racing Car | Logo, branding |
| 📱 | Mobile Phone | QR code instructions |
| 🚀 | Rocket | Footer tagline |
| ⭐ | Star | Ratings, highlights |
| ✓ | Checkmark | Completed steps |
| → | Arrow | Step progression |

---

## Implementation Guide

### Dashboard Creation Checklist

#### 1. Setup CSS Variables
```css
:root {
  /* Copy all color variables from above */
  --deep-blue: #032D60;
  --bright-blue: #00529F;
  /* ... etc */

  /* Copy spacing variables */
  --spacing-xs: 8px;
  /* ... etc */

  /* Copy shadow variables */
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
  /* ... etc */
}
```

#### 2. Import Fonts
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap" rel="stylesheet">
```

Or use system fonts:
```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter',
               'Roboto', 'Helvetica Neue', sans-serif;
}
```

#### 3. Base Styles
```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter',
               'Roboto', 'Helvetica Neue', sans-serif;
  font-size: 16px;
  color: var(--dark-gray);
  background: var(--light-blue-bg);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

h1, h2, h3, h4, h5, h6 {
  font-family: 'Verdana', 'Geneva', sans-serif;
  color: var(--deep-blue);
}
```

#### 4. Page Structure
```html
<div class="dashboard-container">
  <header class="dashboard-header">
    <!-- Logo, title, nav -->
  </header>

  <main class="dashboard-main">
    <div class="dashboard-grid">
      <!-- Cards go here -->
    </div>
  </main>

  <footer class="dashboard-footer">
    <!-- Footer content -->
  </footer>
</div>
```

#### 5. Dashboard Grid Layout
```css
.dashboard-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: radial-gradient(circle at top, var(--bright-blue) 0%, var(--deep-blue) 100%);
}

.dashboard-main {
  flex: 1;
  padding: var(--spacing-lg);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-md);
  max-width: 1400px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .dashboard-main {
    padding: var(--spacing-md);
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
```

#### 6. Reusable Card Component
```css
.dashboard-card {
  background: var(--white);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  transition: all var(--transition-normal);
  animation: fadeInUp 0.5s ease-out;
}

.dashboard-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.card-header {
  font-size: 24px;
  font-weight: 600;
  color: var(--deep-blue);
  margin-bottom: var(--spacing-sm);
  padding-bottom: var(--spacing-sm);
  border-bottom: 2px solid var(--light-blue-bg);
}

.card-body {
  color: var(--dark-gray);
  line-height: 1.6;
}
```

#### 7. Add Animations
```css
/* Copy keyframes from Animation section above */
@keyframes fadeInUp { /* ... */ }
@keyframes pulse { /* ... */ }
/* ... etc */
```

#### 8. Responsive Breakpoints
```css
/* Mobile First Approach */

/* Small devices (phones, up to 768px) */
@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }

  .card-header {
    font-size: 20px;
  }
}

/* Medium devices (tablets, 768px to 1024px) */
@media (min-width: 768px) and (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Large devices (desktops, 1024px and up) */
@media (min-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Ultra-wide (5120×1440) */
@media (min-width: 3840px) {
  .dashboard-grid {
    grid-template-columns: repeat(4, 1fr);
    max-width: 4800px;
  }
}
```

#### 9. Copy Brand Assets
Ensure you have:
- `SF_F1_logo.jpeg` in your public/assets folder
- `F1 25 Trailer 1080p.mp4` (if using video backgrounds)
- `f1_theme_brian_tyler.mp3` (if using audio)

#### 10. Test Responsiveness
- Desktop (1920×1080): Full grid layout
- Tablet (768×1024): 2-column grid
- Mobile (375×667): Single column
- Ultra-wide (5120×1440): 4-column grid with video panels

---

## Quick Start Template

### HTML Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>F1 Simulator Dashboard</title>
  <link rel="stylesheet" href="dashboard.css">
</head>
<body>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <img src="/SF_F1_logo.jpeg" alt="Salesforce F1" class="brand-logo">
      <h1 class="dashboard-title">F1 Simulator Dashboard</h1>
    </header>

    <main class="dashboard-main">
      <div class="dashboard-grid">
        <!-- Card 1 -->
        <div class="dashboard-card">
          <h2 class="card-header">Active Sessions</h2>
          <div class="card-body">
            <!-- Content here -->
          </div>
        </div>

        <!-- Card 2 -->
        <div class="dashboard-card">
          <h2 class="card-header">Leaderboard</h2>
          <div class="card-body">
            <!-- Content here -->
          </div>
        </div>

        <!-- Add more cards as needed -->
      </div>
    </main>

    <footer class="dashboard-footer">
      <p>🚀 Powered by Vibe Coding AI</p>
    </footer>
  </div>
</body>
</html>
```

### CSS Foundation
```css
/* dashboard.css */

/* 1. CSS Variables (copy from Color Palette section) */
:root {
  --deep-blue: #032D60;
  --bright-blue: #00529F;
  --cloud-blue: #00A1E0;
  --gold-yellow: #FFB740;
  --white: #FFFFFF;
  --dark-gray: #3E3E3C;
  --light-gray: #54698D;
  --light-blue-bg: #F3F6F9;
  --success-green: #2E844A;

  --spacing-xs: 8px;
  --spacing-sm: 16px;
  --spacing-md: 24px;
  --spacing-lg: 32px;
  --spacing-xl: 48px;

  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;

  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.12);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.16);

  --transition-fast: 0.2s ease-in-out;
  --transition-normal: 0.3s ease-in-out;
  --transition-slow: 0.5s ease-in-out;
}

/* 2. Base Styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter',
               'Roboto', 'Helvetica Neue', sans-serif;
  font-size: 16px;
  color: var(--dark-gray);
  line-height: 1.5;
}

/* 3. Layout */
.dashboard-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: radial-gradient(circle at top, var(--bright-blue) 0%, var(--deep-blue) 100%);
}

.dashboard-header {
  padding: var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.brand-logo {
  height: 60px;
  width: auto;
}

.dashboard-title {
  color: var(--white);
  font-size: 36px;
  font-weight: 700;
}

.dashboard-main {
  flex: 1;
  padding: var(--spacing-lg);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-md);
  max-width: 1400px;
  margin: 0 auto;
}

/* 4. Card Component */
.dashboard-card {
  background: var(--white);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  transition: all var(--transition-normal);
  animation: fadeInUp 0.5s ease-out;
}

.dashboard-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.card-header {
  font-size: 24px;
  font-weight: 600;
  color: var(--deep-blue);
  margin-bottom: var(--spacing-sm);
  padding-bottom: var(--spacing-sm);
  border-bottom: 2px solid var(--light-blue-bg);
}

.card-body {
  color: var(--dark-gray);
}

/* 5. Footer */
.dashboard-footer {
  padding: var(--spacing-md);
  text-align: center;
  color: var(--white);
  font-size: 14px;
}

/* 6. Animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 7. Responsive */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    text-align: center;
  }

  .dashboard-title {
    font-size: 24px;
  }

  .dashboard-main {
    padding: var(--spacing-md);
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
```

---

## Additional Resources

### File References

**Attract Page Styling:**
- [heroku-app/client/src/pages/AttractScreen.css](heroku-app/client/src/pages/AttractScreen.css) (437 lines)
- [heroku-app/client/src/pages/AttractScreen.tsx](heroku-app/client/src/pages/AttractScreen.tsx)

**Simulator Attract Styling:**
- [server/public/sim-attract.css](server/public/sim-attract.css) (826 lines)
- [server/public/sim-attract.html](server/public/sim-attract.html)

**Global Styles:**
- [heroku-app/client/src/index.css](heroku-app/client/src/index.css) (205 lines)
- [server/public/styles.css](server/public/styles.css) (421 lines)

**Brand Assets:**
- [assets/SF_F1_logo.jpeg](assets/SF_F1_logo.jpeg)
- [assets/F1 25 Trailer 1080p.mp4](assets/F1 25 Trailer 1080p.mp4)
- [assets/f1_theme_brian_tyler.mp3](assets/f1_theme_brian_tyler.mp3)

### Design Tokens Export

For design tools (Figma, Sketch, etc.), here's a JSON export of the design tokens:

```json
{
  "colors": {
    "brand": {
      "deepBlue": "#032D60",
      "brightBlue": "#00529F",
      "cloudBlue": "#00A1E0",
      "goldYellow": "#FFB740"
    },
    "neutrals": {
      "white": "#FFFFFF",
      "darkGray": "#3E3E3C",
      "lightGray": "#54698D",
      "lightBlueBg": "#F3F6F9"
    },
    "states": {
      "success": "#2E844A",
      "warning": "#FFB740",
      "error": "#C23934"
    }
  },
  "spacing": {
    "xs": "8px",
    "sm": "16px",
    "md": "24px",
    "lg": "32px",
    "xl": "48px",
    "2xl": "64px"
  },
  "borderRadius": {
    "sm": "8px",
    "md": "12px",
    "lg": "16px",
    "xl": "24px"
  },
  "typography": {
    "fontFamily": {
      "primary": "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', 'Helvetica Neue', sans-serif",
      "headline": "'Verdana', 'Geneva', sans-serif",
      "monospace": "'Courier New', monospace"
    },
    "fontSize": {
      "display": "54px",
      "h1": "36px",
      "h2": "24px",
      "h3": "20px",
      "bodyLarge": "20px",
      "body": "16px",
      "small": "14px",
      "tiny": "12px"
    },
    "fontWeight": {
      "regular": 400,
      "medium": 500,
      "semibold": 600,
      "bold": 700,
      "extrabold": 900
    }
  },
  "shadows": {
    "sm": "0 2px 8px rgba(0, 0, 0, 0.08)",
    "md": "0 4px 12px rgba(0, 0, 0, 0.12)",
    "lg": "0 8px 24px rgba(0, 0, 0, 0.16)",
    "xl": "0 12px 32px rgba(0, 0, 0, 0.2)"
  }
}
```

---

## Summary

This design system provides everything needed to create a dashboard that matches the F1 Racing Simulator attract pages:

✅ **Complete color palette** with Salesforce-inspired blues and F1 gold accents
✅ **Typography system** with scales, weights, and responsive sizing
✅ **Spacing & layout** tokens for consistent design
✅ **Reusable components** with detailed specifications
✅ **Animation library** with timing and implementation
✅ **Brand assets** and usage guidelines
✅ **Ready-to-use templates** for quick implementation

The design emphasizes **professionalism, energy, and brand consistency** while remaining fully responsive from mobile to ultra-wide displays.

For questions or clarification on any design element, refer to the source files listed in the Additional Resources section.
