# Frontend - University Comparison

Vue.js 3 frontend for University Comparison Web Application.

## Tech Stack

- **Framework**: Vue.js 3 (Composition API)
- **Build Tool**: Vite 5
- **UI Library**: Ant Design Vue 4.x
- **State Management**: Pinia
- **Routing**: Vue Router 4
- **HTTP Client**: Axios
- **Charts**: Chart.js + vue-chartjs

## Project Structure

```
frontend/
├── src/
│   ├── main.js              # App entry point
│   ├── App.vue              # Root component
│   ├── api/                 # API client modules (to be created)
│   ├── components/          # Reusable components (to be created)
│   ├── layouts/             # Layout components (to be created)
│   ├── router/              # Vue Router config
│   ├── stores/              # Pinia stores (to be created)
│   ├── views/               # Page components
│   └── assets/              # Static assets
├── public/                  # Public static files
├── index.html               # HTML template
├── package.json             # Dependencies
├── vite.config.js           # Vite configuration
└── .env                     # Environment variables
```

## Setup Instructions

### 1. Install Dependencies

**Note**: This project requires Node.js v20.19.0+ or v22.12.0+. If you have an older version, you can still install dependencies manually:

```bash
cd frontend
npm install
```

If npm install fails due to Node version, try:

```bash
npm install --legacy-peer-deps
```

### 2. Configure Environment

The `.env` file is already configured with default values. You can modify it if needed:

```
VITE_API_BASE_URL=http://localhost:8000/api
```

### 3. Run Development Server

```bash
cd frontend
npm run dev
```

The app will be available at **http://localhost:5173**

### 4. Build for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

### 5. Preview Production Build

```bash
npm run preview
```

## Development Status

### ✅ Completed

- [x] Project structure setup
- [x] Vite configuration
- [x] Vue Router basic setup
- [x] Ant Design Vue integration
- [x] Basic Home page (placeholder)

### 🚧 In Progress / Planned

**Phase 3: Frontend Core**
- [ ] API client with Axios (axios.js, auth.js, users.js, universities.js)
- [ ] Auth store (Pinia)
- [ ] Router guards for authentication
- [ ] Layout components (DefaultLayout, Header, Footer)
- [ ] Auth views (SignIn, SignUp)
- [ ] Home page (full version)

**Phase 4: University Features**
- [ ] University store (Pinia)
- [ ] Compare store (Pinia)
- [ ] Views: UniversityList, UniversityDetail, CompareUniversities
- [ ] Components: UniversityCard, UniversityTable, FilterBar, ScoreChart

**Phase 5: User Profile & Admin**
- [ ] Views: Profile, AcademicInfo, Admin
- [ ] API clients for user and study background

## Component Mapping (Tkinter → Vue)

| Tkinter File | Vue Component | Route |
|--------------|---------------|-------|
| HomePageUI.py | views/Home.vue | / |
| SignInUI.py | views/SignIn.vue | /signin |
| SignUpUI.py | views/SignUp.vue | /signup |
| RankingListAndTableUI.py | views/UniversityList.vue | /universities |
| UniversityDetailUI.py | views/UniversityDetail.vue | /universities/:id |
| CompareUniUI.py | views/CompareUniversities.vue | /compare |
| PersonalInfoUI.py | views/Profile.vue | /profile |
| PersonalBgUI.py | views/AcademicInfo.vue | /profile/academic |
| AdminUI.py | views/Admin.vue | /admin |

## Available Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
```

## Environment Variables

All environment variables must be prefixed with `VITE_`:

- `VITE_API_BASE_URL` - Backend API base URL (default: http://localhost:8000/api)

Access in code:

```javascript
const apiUrl = import.meta.env.VITE_API_BASE_URL
```

## Ant Design Vue Components

Commonly used components:

- Layout: `a-layout`, `a-layout-header`, `a-layout-content`, `a-layout-footer`
- Form: `a-form`, `a-input`, `a-button`, `a-checkbox`
- Data Display: `a-table`, `a-card`, `a-tag`, `a-typography`
- Navigation: `a-menu`, `a-breadcrumb`, `a-pagination`
- Feedback: `a-message`, `a-notification`, `a-modal`, `a-spin`
- Other: `a-row`, `a-col`, `a-space`, `a-divider`

Documentation: https://antdv.com/components/overview

## Next Steps

1. **Create API client** (src/api/axios.js, auth.js)
2. **Create auth store** (src/stores/auth.js)
3. **Implement SignIn/SignUp pages**
4. **Add router guards for protected routes**
5. **Build university listing and detail pages**

## Notes

- Use Composition API (`<script setup>`) for all components
- Follow Vue 3 best practices
- Use Pinia for state management (not Vuex)
- Ant Design Vue provides both `camelCase` and `kebab-case` naming
- API proxy is configured in vite.config.js (/api → http://localhost:8000)
