// src/RoleGate.jsx
export default function RoleGate({ allow = [], children }) {
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  if (!user?.account_type) return null;
  return allow.includes(user.account_type) ? children : null;
}
