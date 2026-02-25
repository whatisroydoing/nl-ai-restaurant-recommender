# Phase 7 — Mini PRD: Frontend UI

**Phase:** 7  
**Status:** Implementation  
**Reference:** `docs/ARCHITECTURE.md` §2 Phased Delivery, §9 Frontend UI

---

## 1. Objective

Provide a **web-based UI** that lets users enter restaurant preferences and view AI-ranked recommendations with explanations — without calling the API directly.

---

## 2. Scope

- **In scope**
  - Single-page HTML/CSS/JS app (no build step)
  - Preference form: city, location, cuisine, price range, min rating, max results
  - Submit to `POST /recommend` (Phase 4 API)
  - Display ranked recommendation cards with name, explanation, and attributes
  - Loading skeleton animation, empty-results message, error display
  - Zomato-inspired dark theme with `#cb202d` red accents
- **Out of scope**
  - Authentication, user accounts
  - Server-side rendering
  - Multi-page navigation

---

## 3. Design

- **Theme:** Dark background (`#1a1a2e`), Zomato red `#cb202d` gradients
- **Typography:** Google Fonts (Outfit + Inter)
- **Cards:** Glassmorphism with subtle red glow
- **Animations:** Fade-in cards, shimmer loading skeletons, hover micro-effects

---

## 4. Exit Criteria

- Form submits to API and displays results
- Loading, empty, and error states all work
- Responsive on desktop and mobile
