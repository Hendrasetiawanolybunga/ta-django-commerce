# Color Palette Guide for E-Commerce Django Project

## Current Color Palette
- Primary Green: `#08CB00`
- Dark Text/Background: `#000000`
- Light Text/Background: `#EEEEEE`

## Recommended Color Combinations

### 1. Form Elements
- **Input Fields**: 
  - Background: `#EEEEEE` (matches light background)
  - Border: `#DDDDDD` (subtle border)
  - Focus Border: `#08CB00` (primary green)
  - Text: `#000000` (dark text)
  - Placeholder: `#555555` (medium gray for contrast)

- **Focus State**:
  - Background: `#FFFFFF` (white when focused)
  - Box Shadow: `rgba(8, 203, 0, 0.25)` (green tinted shadow)

### 2. Buttons
- **Primary Button**:
  - Background: `linear-gradient(to right, #08CB00, #000000)`
  - Text: `#EEEEEE`
  - Hover Background: `linear-gradient(to right, #000000, #08CB00)`
  - Hover Text: `#EEEEEE`

- **Secondary Button**:
  - Background: `#000000`
  - Text: `#EEEEEE`
  - Hover Background: `#333333`
  - Hover Text: `#EEEEEE`

### 3. Alerts and Messages
- **Success**: `#D4EDDA` background with `#155724` text
- **Info**: `#D1ECF1` background with `#0C5460` text
- **Warning**: `#FFF3CD` background with `#856404` text
- **Error**: `#F8D7DA` background with `#721C24` text

### 4. Additional Accent Colors
- **Light Green (for hover states)**: `#A1FFA1`
- **Medium Gray (for borders and placeholders)**: `#CCCCCC`
- **Dark Gray (for secondary text)**: `#555555`

## Color Theory Explanation

### Why These Colors Work Well Together

1. **Monochromatic Harmony**: 
   - The primary green `#08CB00` creates a strong focal point
   - Light gray `#EEEEEE` provides a neutral background that makes the green pop
   - Black `#000000` adds contrast and sophistication

2. **Accessibility**:
   - High contrast between text (`#000000`) and backgrounds (`#EEEEEE` and `#FFFFFF`)
   - Focus states use the primary green for consistent visual language
   - Sufficient contrast ratios for WCAG compliance

3. **Visual Hierarchy**:
   - Primary green `#08CB00` draws attention to important elements (buttons, links)
   - Neutral grays provide balance and don't compete with the primary color
   - Dark text on light backgrounds ensures readability

### Color Psychology
- **Green (`#08CB00`)**: Represents growth, freshness, and trust - perfect for an e-commerce business
- **Black (`#000000`)**: Adds sophistication and elegance
- **Light Gray (`#EEEEEE`)**: Creates a clean, modern feel without being stark

## Implementation Tips

1. **Consistency**: Use the same color values across all templates
2. **Gradients**: Use the green-to-black gradient sparingly for primary actions
3. **States**: Ensure hover, focus, and active states maintain the color scheme
4. **Feedback**: Use appropriate alert colors for success, warning, and error messages