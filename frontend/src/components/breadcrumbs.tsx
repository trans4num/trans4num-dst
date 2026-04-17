"use client"
import {
    Breadcrumb,
    BreadcrumbItem,
    BreadcrumbLink,
    BreadcrumbList,
    BreadcrumbPage,
    BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Skeleton } from '@/components/ui/skeleton'
import { useRegion } from '@/hooks/use-region'
import { useSingleAlternative } from '@/hooks/use-single-alternative'
import { useParams, usePathname } from 'next/navigation'
import { Fragment, type ReactNode } from 'react'

type TBreadCrumbProps = {
    separator: ReactNode,
    capitalizeLinks?: boolean
}

const Breadcrumbs = ({ separator, capitalizeLinks }: TBreadCrumbProps) => {
    const paths = usePathname()
    const pathNames = paths.split('/').filter(path => path)
    const params = useParams<{regionid: string, id: string}>();
    
    const {region, isLoading: isRegionLoading} = useRegion(params.regionid);
    const { alternative, isLoading: isAlternativeLoading} = useSingleAlternative(params.regionid, params.id);
        
    const getBreadcrumbDetails = (link: string, index: number) => {
        if (params.regionid && region && link === params.regionid) {
            return { 
                label: region.name || link, 
                originalLink: '/region' 
            };
        }
        
        if (params.id && alternative && link === params.id) {
            return { 
                label: alternative.name || link, 
                originalLink: link 
            };
        }
        
        return { 
            label: capitalizeLinks ? link[0].toUpperCase() + link.slice(1) : link, 
            originalLink: link 
        };
    }

    const isLoading = isRegionLoading || isAlternativeLoading;

    return (
        <Breadcrumb>
            <BreadcrumbList>
                {isLoading? (
                    <Skeleton className="h-10 w-full rounded-full " />
                ) : (pathNames.map((link, index) => {
                    const href = `/${pathNames.slice(0, index + 1).join('/')}`
                    const isLast = pathNames.length === index + 1
                    const { label, originalLink } = getBreadcrumbDetails(link, index)
                    
                    return (
                        <Fragment key={index}>
                            {index > 0 && <BreadcrumbSeparator>{separator}</BreadcrumbSeparator>}
                            <BreadcrumbItem>
                                {isLast ? (
                                    <BreadcrumbPage>{label}</BreadcrumbPage>
                                ) : (
                                    <BreadcrumbLink href={href}>{label}</BreadcrumbLink>
                                )}
                            </BreadcrumbItem>
                        </Fragment>
                    )
                }))}
            </BreadcrumbList>
        </Breadcrumb>
    )
}

export default Breadcrumbs