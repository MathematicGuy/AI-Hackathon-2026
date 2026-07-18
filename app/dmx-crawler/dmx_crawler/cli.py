from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from .crawler import Crawler


def _common_crawl_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--category', '--categories', dest='categories', action='append', help='category code(s), repeatable or comma-separated')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--force', action='store_true', help='ignore incremental next_due_at state')
    parser.add_argument('--only-due', action='store_true', help='explicitly use incremental next_due_at filtering (default)')


def _categories(args: argparse.Namespace) -> list[str] | None:
    values = getattr(args, 'categories', None)
    if not values:
        return None
    return [part.strip() for value in values for part in str(value).split(',') if part.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='dmx', description='Respectful Điện Máy XANH product crawler')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('init-db', help='initialize SQLite or verify migrated PostgreSQL, then seed config')
    sub.add_parser('doctor', help='validate local configuration and database')

    discover = sub.add_parser('discover', help='discover product URLs (sitemap first)')
    discover.add_argument('--category', '--categories', dest='categories', action='append')
    discover.add_argument('--source', choices=('auto', 'sitemap', 'category'), default='auto')
    discover.add_argument('--limit', type=int, default=None)
    discover.add_argument('--max-sitemaps', type=int, default=None)

    crawl = sub.add_parser('crawl', help='crawl product data')
    crawl_sub = crawl.add_subparsers(dest='crawl_command', required=True)
    products = crawl_sub.add_parser('products', aliases=['product'], help='crawl common product facts')
    _common_crawl_flags(products)
    location = crawl_sub.add_parser('location', help='crawl one location in its own session')
    location.add_argument('--location', required=True, dest='location_code')
    _common_crawl_flags(location)
    all_locations = crawl_sub.add_parser('all-locations', help='crawl every configured location independently')
    _common_crawl_flags(all_locations)

    # Explicit aliases make shell automation readable while retaining the
    # nested ``crawl`` command required by the project brief.
    product_alias = sub.add_parser('crawl-product', aliases=['crawl-products'], help='alias for crawl products')
    product_alias.add_argument('--url', default=None, help='optional single product URL')
    _common_crawl_flags(product_alias)
    location_alias = sub.add_parser('crawl-location', help='alias for crawl location')
    location_alias.add_argument('--location', required=True, dest='location_code')
    _common_crawl_flags(location_alias)
    all_alias = sub.add_parser('crawl-all-locations', help='alias for crawl all-locations')
    _common_crawl_flags(all_alias)

    retry = sub.add_parser('retry-errors', help='retry unresolved transient errors')
    retry.add_argument('--limit', type=int, default=None)

    export = sub.add_parser('export', help='export current product/location state')
    export.add_argument('--format', choices=('json', 'csv'), default='json')
    export.add_argument('--output', default=None)
    export.add_argument('--limit', type=int, default=100)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    crawler = Crawler()
    try:
        if args.command == 'init-db':
            crawler.initialize()
            print(json.dumps({'ok': True, 'database': crawler.settings.database_url}, ensure_ascii=False))
        elif args.command == 'doctor':
            result = crawler.doctor()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['ok'] else 1
        elif args.command == 'discover':
            result = crawler.discover(_categories(args), args.source, args.limit, args.max_sitemaps)
            print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
        elif args.command in {'crawl-product', 'crawl-products'}:
            if getattr(args, 'url', None):
                result = crawler.crawl_url(args.url, _categories(args), force=args.force)
            else:
                result = crawler.crawl_products(_categories(args), args.limit, args.force)
            print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
        elif args.command in {'crawl-location'}:
            result = crawler.crawl_location(args.location_code, _categories(args), args.limit, args.force)
            print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
        elif args.command in {'crawl-all-locations'}:
            result = crawler.crawl_all_locations(_categories(args), args.limit, args.force)
            print(json.dumps([item.as_dict() for item in result], ensure_ascii=False, indent=2))
        elif args.command == 'crawl':
            if args.crawl_command in {'products', 'product'}:
                result = crawler.crawl_products(_categories(args), args.limit, args.force)
                print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
            elif args.crawl_command == 'location':
                result = crawler.crawl_location(args.location_code, _categories(args), args.limit, args.force)
                print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
            else:
                result = crawler.crawl_all_locations(_categories(args), args.limit, args.force)
                print(json.dumps([item.as_dict() for item in result], ensure_ascii=False, indent=2))
        elif args.command == 'retry-errors':
            result = crawler.retry_errors(args.limit)
            print(json.dumps([item.as_dict() for item in result], ensure_ascii=False, indent=2))
        elif args.command == 'export':
            text = crawler.export(args.format, args.output, args.limit)
            if not args.output:
                print(text)
            else:
                print(json.dumps({'ok': True, 'output': args.output, 'rows': len(crawler.db.export_current(args.limit))}, ensure_ascii=False))
        return 0
    except KeyboardInterrupt:
        print('interrupted; no anti-bot bypass was attempted', file=sys.stderr)
        return 130
    except Exception as exc:
        print(f'error: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2
    finally:
        crawler.db.close()


if __name__ == '__main__':
    raise SystemExit(main())
