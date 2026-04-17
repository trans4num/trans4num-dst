import { Link as RouterLink, type LinkProps as RouterLinkProps } from "react-router-dom";

type Props = RouterLinkProps & React.AnchorHTMLAttributes<HTMLAnchorElement> & { href?: string };

export default function Link({ href, to, ...props }: Props) {
  return <RouterLink to={href ?? to ?? "/"} {...props} />;
}
