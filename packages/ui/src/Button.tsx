import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "quiet";

type TanimButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  children: ReactNode;
};

const variantClass: Record<ButtonVariant, string> = {
  primary: "primary-button",
  secondary: "secondary-button",
  quiet: "quiet-button",
};

export function TanimButton({ variant = "secondary", children, ...rest }: TanimButtonProps) {
  return (
    <button className={variantClass[variant]} type={rest.type ?? "button"} {...rest}>
      {children}
    </button>
  );
}
