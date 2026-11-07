import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api, message } from "../api";
import { Badge, ErrorBox } from "../shared";

const schema = z.object({
  email: z.string().trim().email("Enter a valid email address.").max(200),
  password: z.string().min(12, "Use at least 12 characters.").max(128),
});

export default function Register() {
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) });
  return (
    <div className="login">
      <div className="login-intro">
        <Link className="brand" to="/">
          <span className="logo">
            <ShieldCheck />
          </span>
          FederGuard AI
        </Link>
        <div>
          <div className="eyebrow">GET STARTED</div>
          <h1>
            One workspace.
            <br />A collective defense.
          </h1>
          <p>
            Create an account to explore fraud intelligence in your own demo
            workspace.
          </p>
        </div>
        <small>Academic demonstration · All records are synthetic</small>
      </div>
      <form
        onSubmit={handleSubmit(async ({ email, password }) => {
          setError("");
          try {
            await api.post("/auth/register", { email, password });
            navigate("/login", {
              replace: true,
              state: { registeredEmail: email },
            });
          } catch (e) {
            setError(message(e));
          }
        })}
      >
        <Badge>CREATE ACCOUNT</Badge>
        <h1>Create your account</h1>
        <p>Start exploring your fraud intelligence workspace.</p>
        <label>
          Email address
          <input
            type="email"
            autoComplete="username"
            {...register("email")}
            aria-invalid={!!errors.email}
          />
        </label>
        {errors.email && <ErrorBox error={errors.email.message || ""} />}
        <label>
          Password
          <input
            type="password"
            autoComplete="new-password"
            {...register("password")}
            aria-invalid={!!errors.password}
          />
        </label>
        {errors.password && <ErrorBox error={errors.password.message || ""} />}
        <ErrorBox error={error} />
        <button className="btn" disabled={isSubmitting}>
          {isSubmitting ? "Creating account…" : "Create account"}
          <ArrowRight size={17} />
        </button>
        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </div>
  );
}
