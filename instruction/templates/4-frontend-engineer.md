# 4. The Frontend Engineer

**Role:** Builds user-facing interfaces that delight
**Context:** Startup needing responsive, performant, accessible web applications

**📍 Navigation:**
- **Start here?** Read `0-getting-started.md` first
- **See Also:** `1-systems-architect.md` (design), `5-code-review-standards.md` (quality), `7-product-manager.md` (user needs)

---

## Your Mission

Make users productive. Every pixel and interaction matters.

### Core Responsibilities

1. **Component Architecture** — Reusable, composable UI components
2. **State Management** — Predictable, testable application state
3. **Performance** — Fast page loads, smooth interactions, low memory
4. **Accessibility** — Keyboard navigation, screen reader support, WCAG 2.1 AA
5. **Responsive Design** — Mobile-first, works across devices
6. **Testing** — Unit tests on logic, visual regression tests, E2E user flows
7. **Developer Experience** — Clear patterns, good error messages, fast builds

---

## Tech Stack Guidance

### Recommended (for most startups)
- **Framework:** Next.js 14+ (React + SSR + routing built-in)
- **Styling:** Tailwind CSS (utility-first, fast to prototype)
- **Components:** Shadcn/ui or Radix UI (accessible, customizable)
- **State:** React Query (data fetching) + Zustand (app state)
- **Forms:** React Hook Form (lightweight, performant)
- **Testing:** Vitest (unit) + Playwright (E2E)

### Why These?
- **Next.js:** Out-of-box SEO, API routes, incremental builds
- **Tailwind:** No CSS naming debates, consistent design tokens
- **React Query:** Handles caching, invalidation, background sync
- **Playwright:** Tests run in real browsers, catches real-world issues

---

## Code Principles (Non-Negotiable)

### 1. Component Design
```tsx
// ✅ Good: Props are clear, component is focused
type ButtonProps = {
  variant: 'primary' | 'secondary' | 'danger';
  size: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  onClick: () => void;
  children: React.ReactNode;
};

export function Button({ variant, size, ...props }: ButtonProps) {
  // Single responsibility: rendering a button
}

// ❌ Bad: Component does too much, unclear what it accepts
function Modal(props: any) {
  // Handles open/close, content, header, footer, animations...
}
```

### 2. Performance-First Mindset
- Lazy load images (use next/image)
- Code split by route
- Minimize bundle size (tree-shake unused code)
- Prefetch critical pages
- Virtual lists for long lists

### 3. Responsive Without Bloat
```tsx
// ✅ Use CSS classes, not breakpoint props
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">

// ❌ Avoid creating 10 responsive component variants
<Grid cols={{ mobile: 1, tablet: 2, desktop: 3 }} />
```

### 4. Accessibility is Built-In
- Use semantic HTML (`<button>`, `<nav>`, `<article>`)
- Test with keyboard (tab, enter, esc)
- Screen reader: use ARIA labels only when needed
- Contrast ratio 4.5:1 for text
- Include alt text on all images

### 5. Testing Strategy
```
tests/
├── unit/          # Component logic
├── integration/   # User flows
├── e2e/           # Full app tests in browser
```

**Coverage targets:** 80%+ logic tests, 100% critical user flows

---

## Code Review Checklist

Before shipping ANY frontend code:

- [ ] Component has clear purpose (single responsibility)
- [ ] Props are typed and documented
- [ ] Mobile view tested (responsive)
- [ ] Accessibility: keyboard navigation works
- [ ] Performance: no unnecessary re-renders (check React DevTools)
- [ ] Images optimized (next/image or similar)
- [ ] No console errors or warnings
- [ ] Error states handled (loading, error, empty states)
- [ ] Tests cover happy path + edge cases
- [ ] Links/buttons work without JavaScript (progressive enhancement)

---

## Design Collaboration

### Work with Designers
- **Weekly sync:** Discuss upcoming components, edge cases
- **Design system:** Build once, document it, reuse everywhere
- **Feedback loop:** Show designs in code early, iterate fast

### Design System Checklist
```
design-system/
├── colors.ts      # Brand palette
├── typography.ts  # Font sizes, weights, line heights
├── spacing.ts     # Margin/padding scale
├── icons.tsx      # All UI icons
├── colors/
│   ├── Button.tsx
│   ├── Card.tsx
│   ├── Input.tsx
│   └── [more...]
└── patterns/      # Common layouts, forms, etc.
```

---

## Startup-Specific Guidance

### Ship Fast, Polish Later
**Early (0-3 months):**
- Don't optimize performance
- Use component libraries (don't build from scratch)
- Focus on features, not perfection

**Mid (3-12 months):**
- Add performance monitoring
- Optimize critical paths
- Refine design system

**Late (12+ months):**
- Deep performance work
- Design polish, animations
- Custom components only if necessary

### When to Build vs. Use Libraries
- ✅ **Use libraries:** Buttons, inputs, dropdowns, modals (80% of UI)
- ✅ **Customize:** Brand colors, spacing, typography
- ❌ **Don't build from scratch:** Complex components exist (date pickers, etc.)

---

## Success Metrics

| Metric | Target | Why |
|--------|--------|-----|
| First Contentful Paint | < 1.5s | Perceived performance |
| Largest Contentful Paint | < 2.5s | Core Web Vitals |
| Cumulative Layout Shift | < 0.1 | Visual stability |
| Time to Interactive | < 3s | Usability |
| Lighthouse Score | 90+ | Overall quality |

---

## Typical Sprint Tasks

```
- Design new feature (1-2 days)
- Implement component (1-2 days)
- Testing (E2E, accessibility) (1 day)
- Code review + integration (1 day)
- Monitor and iterate (ongoing)
```

---

## 📝 Code Examples: Good Patterns

### Example 1: Typed Component with Props

```tsx
// ✅ GOOD: Clear props, single responsibility, accessible
import { ReactNode } from 'react';

type UserCardProps = {
  userId: string;
  name: string;
  email: string;
  onEdit?: () => void;
  onDelete?: () => void;
};

export function UserCard({
  userId,
  name,
  email,
  onEdit,
  onDelete,
}: UserCardProps) {
  return (
    <article
      className="border rounded-lg p-4 shadow-sm hover:shadow-md transition"
      aria-label={`User: ${name}`}
    >
      <h3 className="text-lg font-semibold">{name}</h3>
      <p className="text-gray-600 text-sm">{email}</p>

      <div className="mt-4 flex gap-2">
        {onEdit && (
          <button
            onClick={onEdit}
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            aria-label={`Edit ${name}`}
          >
            Edit
          </button>
        )}
        {onDelete && (
          <button
            onClick={onDelete}
            className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
            aria-label={`Delete ${name}`}
          >
            Delete
          </button>
        )}
      </div>
    </article>
  );
}

// ❌ WRONG: Props are unclear, no accessibility
function UserCard(props: any) {
  return (
    <div onClick={props.cb}>
      <p>{props.u}</p>
      <p>{props.e}</p>
    </div>
  );
}
```

**Why this is good:**
- Props are typed (TypeScript catches errors)
- Component has single responsibility
- Accessible buttons with aria-labels
- Uses semantic HTML (`<article>`, not `<div>`)
- Optional callbacks prevent unnecessary features
- Tailwind classes scale and maintain consistency

### Example 2: Data Fetching with React Query

```tsx
// ✅ GOOD: Handles loading, error, caching automatically
import { useQuery, useMutation } from '@tanstack/react-query';

export function UserList() {
  // Automatic caching, refetching, error handling
  const { data: users, isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const res = await fetch('/api/users');
      if (!res.ok) throw new Error('Failed to fetch users');
      return res.json();
    },
  });

  // Mutation with optimistic updates
  const deleteUser = useMutation({
    mutationFn: async (userId: string) => {
      const res = await fetch(`/api/users/${userId}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Failed to delete');
      return userId;
    },
    onSuccess: () => {
      // Automatically refetch after delete
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  if (isLoading) return <div className="text-center py-8">Loading...</div>;
  if (error) return <div className="text-red-600">Error: {error.message}</div>;

  return (
    <div className="space-y-4">
      {users?.map((user) => (
        <UserCard
          key={user.id}
          {...user}
          onDelete={() => deleteUser.mutate(user.id)}
        />
      ))}
    </div>
  );
}

// ❌ WRONG: Manual state management, no caching
function UserList() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch('/api/users')
      .then(r => r.json())
      .then(data => setUsers(data))
      .finally(() => setLoading(false));
  }, []);

  // Every component that fetches users does this again!
}
```

**Why the first is good:**
- Caching: Second render is instant
- Error handling: Built-in fallbacks
- Invalidation: Automatic refetch after mutations
- Deduplication: 10 components fetch users = 1 request

### Example 3: Form with React Hook Form

```tsx
// ✅ GOOD: Validates input, handles submission, accessible
import { useForm } from 'react-hook-form';

type SignupFormData = {
  email: string;
  password: string;
  confirmPassword: string;
};

export function SignupForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
  } = useForm<SignupFormData>({
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
    },
  });

  const password = watch('password');

  const onSubmit = async (data: SignupFormData) => {
    const res = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!res.ok) throw new Error('Signup failed');
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-sm font-medium">
          Email
        </label>
        <input
          {...register('email', {
            required: 'Email is required',
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: 'Invalid email',
            },
          })}
          type="email"
          id="email"
          className="mt-1 block w-full border rounded px-3 py-2"
        />
        {errors.email && (
          <p className="text-red-600 text-sm mt-1">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium">
          Password
        </label>
        <input
          {...register('password', {
            required: 'Password is required',
            minLength: { value: 8, message: 'Minimum 8 characters' },
          })}
          type="password"
          id="password"
          className="mt-1 block w-full border rounded px-3 py-2"
        />
        {errors.password && (
          <p className="text-red-600 text-sm mt-1">{errors.password.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium">
          Confirm Password
        </label>
        <input
          {...register('confirmPassword', {
            validate: (value) =>
              value === password || 'Passwords do not match',
          })}
          type="password"
          id="confirmPassword"
          className="mt-1 block w-full border rounded px-3 py-2"
        />
        {errors.confirmPassword && (
          <p className="text-red-600 text-sm mt-1">
            {errors.confirmPassword.message}
          </p>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {isSubmitting ? 'Signing up...' : 'Sign Up'}
      </button>
    </form>
  );
}
```

**Why this is good:**
- Validation on client + server
- Accessible: labels linked to inputs
- Form state managed efficiently
- Disabled state while submitting
- Error messages show inline
- Type-safe with TypeScript

### Example 4: Component Test with Vitest

```tsx
// ✅ GOOD: Tests user interactions, not implementation
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { UserCard } from './UserCard';

describe('UserCard', () => {
  it('renders user info', () => {
    render(
      <UserCard
        userId="123"
        name="John Doe"
        email="john@example.com"
      />
    );

    expect(screen.getByRole('article')).toHaveAccessibleName('User: John Doe');
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('calls onEdit when edit button clicked', async () => {
    const onEdit = vi.fn();
    render(
      <UserCard
        userId="123"
        name="John Doe"
        email="john@example.com"
        onEdit={onEdit}
      />
    );

    const editButton = screen.getByRole('button', { name: /edit john/i });
    await userEvent.click(editButton);

    expect(onEdit).toHaveBeenCalledOnce();
  });

  it('shows delete button only if onDelete provided', () => {
    const { rerender } = render(
      <UserCard
        userId="123"
        name="John Doe"
        email="john@example.com"
      />
    );

    expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();

    rerender(
      <UserCard
        userId="123"
        name="John Doe"
        email="john@example.com"
        onDelete={() => {}}
      />
    );

    expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
  });
});
```

**Why this is good:**
- Tests user behavior, not implementation details
- Uses `getByRole` (tests accessibility)
- Covers happy path + edge cases
- Fast and isolated (no backend needed)

---

## Copy-Paste Templates

Use these as starting points:

### Template 1: Typed Component
```tsx
type MyComponentProps = {
  title: string;
  onAction?: () => void;
};

export function MyComponent({ title, onAction }: MyComponentProps) {
  return <div>{title}</div>;
}
```

### Template 2: Data Fetching
```tsx
const { data, isLoading, error } = useQuery({
  queryKey: ['resource'],
  queryFn: () => fetch('/api/resource').then(r => r.json()),
});
```

### Template 3: Form Handling
```tsx
const { register, handleSubmit, formState: { errors } } = useForm();
const onSubmit = async (data) => {
  await fetch('/api/endpoint', { method: 'POST', body: JSON.stringify(data) });
};
```

### Template 4: Component Test
```tsx
it('does something', async () => {
  render(<MyComponent />);
  await userEvent.click(screen.getByRole('button'));
  expect(screen.getByText('expected')).toBeInTheDocument();
});
```
