---
name: Institutional Trust
colors:
  surface: '#f8fafb'
  surface-dim: '#d8dadb'
  surface-bright: '#f8fafb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f5'
  surface-container: '#eceeef'
  surface-container-high: '#e6e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#444651'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#eff1f2'
  outline: '#747682'
  outline-variant: '#c4c6d3'
  surface-tint: '#3f5aa8'
  primary: '#00246b'
  on-primary: '#ffffff'
  primary-container: '#1c3b88'
  on-primary-container: '#8fa9fd'
  inverse-primary: '#b4c5ff'
  secondary: '#006a68'
  on-secondary: '#ffffff'
  secondary-container: '#6ff4f1'
  on-secondary-container: '#006e6d'
  tertiary: '#00295a'
  on-tertiary: '#ffffff'
  tertiary-container: '#003f82'
  on-tertiary-container: '#7dadff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#24428f'
  secondary-fixed: '#72f6f4'
  secondary-fixed-dim: '#51dad7'
  on-secondary-fixed: '#00201f'
  on-secondary-fixed-variant: '#00504f'
  tertiary-fixed: '#d7e3ff'
  tertiary-fixed-dim: '#aac7ff'
  on-tertiary-fixed: '#001b3e'
  on-tertiary-fixed-variant: '#00458e'
  background: '#f8fafb'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
  institutional-navy: '#1C3B88'
  yono-cyan: '#00B1AF'
  background-grey: '#F1F3F4'
  text-main: '#212529'
  border-standard: '#D1D5DB'
typography:
  headline-lg:
    fontFamily: Arimo
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-lg-mobile:
    fontFamily: Arimo
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 28px
  headline-md:
    fontFamily: Arimo
    fontSize: 20px
    fontWeight: '700'
    lineHeight: 26px
  body-lg:
    fontFamily: Arimo
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Arimo
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Arimo
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Arimo
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 20px
    letterSpacing: 0.5px
  label-md:
    fontFamily: Arimo
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.3px
  label-sm:
    fontFamily: Arimo
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.2px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  margin-mobile: 16px
  margin-desktop: 48px
  gutter: 16px
  density-xs: 4px
  density-sm: 8px
  density-md: 12px
  container-max: 1200px
---

## Brand & Style

This design system is built for the Indian public sector banking context, where the primary objective is to convey institutional stability, scale, and accessibility. The visual identity reflects a transition from traditional legacy systems to a digital-first approach, maintaining a sense of authority while improving functional density.

The design style is **Corporate / Modern** with a lean toward **Utilitarianism**. It prioritizes information hierarchy and data density over decorative whitespace. The aesthetic is clean and structured, utilizing a signature dual-tone header system and a rigid grid to organize complex financial data. The emotional goal is to evoke a sense of security, officiality, and reliability for millions of diverse users.

## Colors

The palette is anchored by a deep **Institutional Navy**, which provides the formal weight required for a major bank. This is contrasted by a vibrant **YONO Cyan**, used strategically for digital calls-to-action and modern sub-brands to signify technological advancement.

A light, neutral grey serves as the canvas, preventing eye strain in high-density data views. The signature dual-tone header style should utilize the Institutional Navy for the primary navigation level and the brighter tertiary blue for secondary utilities. Status colors (Success, Warning, Error) must be highly saturated to ensure clarity against the white and grey backgrounds.

## Typography

The typography uses **Arimo**, a neutral, humanist sans-serif that serves as a highly readable, modern alternative to Arial. It maintains the practical, dense feel required for financial statements and complex forms while offering better legibility on mobile screens.

The type scale is compressed to support information density. Headlines are bold and authoritative, while body text and labels are kept compact. In data-heavy tables, the "body-sm" and "label-sm" roles should be the primary choice to maximize visible content without horizontal scrolling. Use tight line-heights (1.2x to 1.4x) to maintain the signature "dense" banking aesthetic.

## Layout & Spacing

This design system employs a **Fixed Grid** on desktop (12 columns, 1200px max-width) and a **Fluid Grid** on mobile. The spacing philosophy is based on a 4px baseline, but with a preference for "tight" padding to enable high information density.

Layouts should be structured horizontally where possible, using tables and list views rather than large cards. Margins are kept conservative (16px on mobile) to allow content to span as much width as possible. The signature header must be sticky, utilizing the top 40px for global links and the subsequent 64px for the primary brand and navigation.

## Elevation & Depth

To maintain a utilitarian and professional feel, this design system avoids heavy shadows and decorative blurs. Depth is primarily conveyed through **Tonal Layers** and **Low-Contrast Outlines**.

1.  **Background:** Surfaces use `#F1F3F4`.
2.  **Containers:** Primary content areas are pure white (`#FFFFFF`) with a 1px solid border in `#D1D5DB`.
3.  **Active States:** Use a subtle 2px bottom border in Institutional Navy rather than a shadow to indicate selection.
4.  **Elevation:** For modals or dropdowns, use a minimal, crisp shadow (e.g., `0px 2px 4px rgba(0,0,0,0.1)`) to separate the element from the base layer without creating a "floating" effect.

## Shapes

The shape language is rigid and disciplined. A minimal corner radius of **2px** is applied to buttons, input fields, and cards. This near-sharp execution reinforces the serious, institutional nature of the bank. 

Avoid circles or large pill shapes, except for small status indicators (chips) which may use a slightly more rounded profile (4px) to distinguish them from actionable buttons. Icons should be functional and linear, following a consistent 2px stroke weight.

## Components

### Buttons
Primary buttons use a solid `Institutional-Navy` background with white text and 2px rounded corners. Secondary buttons use the `YONO-Cyan` for digital-specific actions (like Quick Pay). Use a "compact" variant for table-row actions with reduced vertical padding.

### Input Fields
Inputs are rectangular with a 1px border. The focus state uses a 2px border of `Institutional-Navy`. Labels should be persistent or placed directly above the field in `label-md` to ensure clarity for users with varying levels of digital literacy.

### Dual-Tone Header
A mandatory component consisting of a top bar in `Institutional-Navy` for corporate links/language selection, and a bottom bar in `Tertiary-Blue` for the main navigation menu and search.

### Data Tables
The core component of the system. Tables should have zebra-striping using `#F1F3F4`, a bold header row in `Institutional-Navy` with white text, and tight cell padding. Borders should be visible but low-contrast.

### Cards & Containers
Used sparingly for dashboard summaries. Cards are white with a 1px border and no shadow. They should be used to group related information like "Account Balance" or "Recent Transactions" rather than for singular stylistic choices.

### Chips & Badges
Small, rectangular tags with 2px radius used for transaction status (e.g., "Pending", "Success"). Use high-contrast background colors with dark text for maximum legibility.