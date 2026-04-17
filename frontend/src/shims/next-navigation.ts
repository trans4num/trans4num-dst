import {
  useLocation,
  useNavigate,
  useParams as useRouteParams,
  useSearchParams as useRouterSearchParams,
} from "react-router-dom";

export const useRouter = () => {
  const navigate = useNavigate();

  return {
    push: (href: string) => navigate(href),
    replace: (href: string) => navigate(href, { replace: true }),
    back: () => navigate(-1),
    refresh: () => window.location.reload(),
  };
};

export const usePathname = () => useLocation().pathname;

export const useSearchParams = () => {
  const [searchParams] = useRouterSearchParams();
  return searchParams;
};

export const useParams = <T extends Record<string, string | undefined>>() =>
  useRouteParams() as T;
