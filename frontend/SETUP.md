# University Comparison Frontend - Vue.js

A modern web frontend for comparing universities worldwide, built with Vue 3, Ant Design Vue, and Vite.

## Features Implemented

### 1. **Authentication System**
- Sign Up (email, password, first name, last name)
- Sign In (email and password)
- Password management
- Logout with token invalidation
- JWT token-based authentication with refresh tokens

### 2. **Universities Listing & Discovery**
- View all universities with rankings and ratings
- Search universities by name
- Advanced filtering by:
  - Country
  - Region
  - Ranking range
- Side-by-side university comparison
- Detailed university profiles

### 3. **University Details**
- Overall information and rankings
- Tuition fees and scholarship availability
- Student demographics (total, international, domestic)
- International student percentages
- Entry requirements for Bachelor and Master degrees
  - SAT, GRE, GMAT, ACT scores
  - IELTS and TOEFL requirements
  - GPA requirements
- Academic scores by category

### 4. **Comparison Tool**
- Add multiple universities to compare
- Side-by-side comparison table
- Entry requirements comparison chart
- Scholarship and admission rates comparison

### 5. **User Profile Management**
- View and edit personal information
- Update profile (name, phone, DOB, gender, country)
- Change password
- Manage study background information

### 6. **Responsive Design**
- Mobile-friendly interface
- Tablet optimization
- Desktop experience
- Ant Design Vue UI components

## API Integration

The frontend integrates with the following API endpoints:

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout

### Users
- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update profile
- `PUT /api/users/me/password` - Change password
- `GET /api/users/{userId}` - Get user by ID

### Universities
- `GET /api/universities` - List all universities
- `GET /api/universities/{id}` - Get university details
- `GET /api/universities/search?q=query` - Search universities
- `GET /api/universities/filter` - Filter universities by criteria
- `GET /api/universities/{id}/entry-requirements` - Get entry requirements
- `POST /api/universities/compare` - Compare multiple universities
- `POST /api/universities/chart-data` - Get chart data for comparison

### Countries
- `GET /api/countries` - Get all countries

### Study Background
- `GET /api/study-bg` - Get user's study background
- `PUT /api/study-bg` - Update study background

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable Vue components
│   ├── views/              # Page components
│   │   ├── Home.vue        # Landing page
│   │   ├── Login.vue       # Login page
│   │   ├── Signup.vue      # Registration page
│   │   ├── Dashboard.vue   # Main dashboard layout
│   │   ├── Universities.vue # Universities listing & filtering
│   │   ├── UniversityDetail.vue # University details
│   │   ├── Comparison.vue  # Comparison tool
│   │   └── Profile.vue     # User profile management
│   ├── services/
│   │   └── api.js          # API client with axios
│   ├── stores/
│   │   └── auth.js         # Pinia auth store
│   ├── router/
│   │   └── index.js        # Vue Router configuration
│   ├── App.vue             # Root component
│   └── main.js             # Application entry point
├── package.json            # Dependencies
├── vite.config.js         # Vite configuration
└── index.html             # HTML template
```

## Installation & Setup

### 1. Install dependencies
```bash
cd frontend
npm install
```

### 2. Update API URL (if needed)
Edit `src/services/api.js` and change `API_BASE_URL` if your backend is not at `http://localhost:8000`:

```javascript
const API_BASE_URL = 'http://your-backend-url/api'
```

### 3. Add missing dependencies
```bash
npm install dayjs chart.js vue-chartjs
```

### 4. Start development server
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### 5. Build for production
```bash
npm run build
```

## Usage Flow

### 1. **First Time User**
1. Visit the landing page
2. Click "Sign Up"
3. Fill in registration form (name, email, password)
4. Click "Create Account"
5. Log in with credentials

### 2. **Finding Universities**
1. Log in to the application
2. Navigate to "Universities" from the menu
3. Use search to find specific universities
4. Use "Advanced Filter" to filter by country, region, ranking
5. Click "View Details" on any university card to see full information

### 3. **Comparing Universities**
1. From university detail page, click "Add to Compare"
2. Add multiple universities (up to 5 recommended)
3. Navigate to "Compare" page to view side-by-side comparison
4. View detailed comparison table and entry requirements chart

### 4. **Managing Profile**
1. Click on user dropdown (top right)
2. Select "Profile"
3. Update personal information, password, or study background
4. Changes are saved to your account

## Authentication Flow

The application uses JWT tokens for authentication:

1. **Login**: User credentials are sent to backend, receives access and refresh tokens
2. **Token Storage**: Tokens are stored in localStorage
3. **API Requests**: All API requests include the access token in Authorization header
4. **Token Refresh**: When access token expires, refresh token is used to get a new one
5. **Logout**: Refresh token is invalidated on the backend

## Features by Page

### Landing Page (`/`)
- Hero section with call-to-action
- Feature highlights
- Sign up/login buttons
- Footer with links

### Login Page (`/login`)
- Email and password inputs
- Form validation
- Error handling
- Link to signup for new users

### Signup Page (`/signup`)
- First name, last name inputs
- Email input with validation
- Password with confirmation
- Password strength validation
- Link to login for existing users

### Dashboard (`/home`)
- Navigation header with menu
- User dropdown with logout
- Router outlet for sub-pages

### Universities Page (`/home/universities`)
- Search bar for university names
- Advanced filter modal
- Grid of university cards
- Click to view details

### University Detail Page (`/university/:id`)
- University header with logo and basic info
- Tabs for different sections:
  - Details (fees, scholarships, student info)
  - Entry Requirements (bachelor/master)
  - Scores (academic performance metrics)
- Add to Compare button

### Comparison Page (`/home/comparison`)
- Add universities by ID
- View comparison table
- Entry requirements chart
- Remove individual universities
- Clear all button

### Profile Page (`/home/profile`)
- Tabs for Personal Info, Password, Study Background
- Edit profile form
- Change password form
- Study background form

## Styling

The application uses Ant Design Vue for UI components and custom SCSS for additional styling. The design is responsive and works well on all device sizes.

Key colors:
- Primary: #1890ff (Ant Design Blue)
- Gradient: #667eea to #764ba2
- Background: #f5f5f5

## Error Handling

- API errors are caught and displayed as user-friendly messages
- Form validation prevents invalid submissions
- Authentication errors redirect to login page
- Network errors show error messages

## Known Limitations

1. Profile updates reload the page (security measure)
2. Comparison limited to Universities list returned by API
3. Chart visualization requires additional UI improvements

## Future Enhancements

1. Add user preferences and favorite universities
2. Implement AI-powered recommendations
3. Add scholarship opportunities search
4. Implement chat with students feature
5. Add university news and events
6. Export comparison as PDF
7. Add more advanced filtering options
8. Implement rating and reviews system

## Support

For issues or questions, contact the development team or file an issue in the project repository.

---

Built with ❤️ using Vue 3, Vite, and Ant Design Vue
