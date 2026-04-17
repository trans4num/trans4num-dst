type Props = React.ImgHTMLAttributes<HTMLImageElement> & {
  src: string;
  alt: string;
};

export default function Image({ src, alt, ...props }: Props) {
  return <img src={src} alt={alt} {...props} />;
}
