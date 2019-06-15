import * as PropTypes from 'prop-types';
import queryString from 'query-string';
import React, { Component } from 'react';
import gql from 'graphql-tag';

import PriceFilter from './PriceFilter';
import ProductFilters from './ProductFilters';
import ProductList from './ProductList';
import SortBy from './SortBy';
import { isMobile } from '../utils';
import { convertSortByFromObject, convertSortByFromString } from './utils';

const WAIT_FOR_INPUT = 200;

class CategoryPage extends Component {
  constructor (props) {
    super(props);
    this.state = {
      filtersMenu: !isMobile(),
      loading: false
    };
    this.timer = new Date();
  }

  static propTypes = {
    attributes: PropTypes.array,
    category: PropTypes.object,
    products: PropTypes.array
  };

  incrementProductsCount = () => {
    this.props.data.refetch({
      first: this.props.data.variables.first + this.props.PAGINATE_BY
    });
  };

  setSorting = (value) => {
    this.props.data.refetch({
      sortBy: convertSortByFromString(value)
    });
  };

  toggleMenu = (target) => {
    this.setState({
      filtersMenu: !target
    });
  };

  static fragments = {
    category: gql`
      fragment CategoryPageFragmentQuery on Category {
        id
        name
        url
        ancestors(last: 5) {
          edges {
            node {
              name
              id
              url
            }
          }
        }
        children(first: 5) {
          edges {
            node {
              name
              id
              url
              slug
            }
          }
        }
      }
    `
  };

  clearFilters = () => {
    this.props.data.refetch({
      attributesFilter: [],
      minPrice: null,
      maxPrice: null
    });
  };

  updateAttributesFilter = (key) => {
    const index = this.props.data.variables.attributesFilter.indexOf(key);
    this.props.data.variables.attributesFilter = this.props.data.variables.attributesFilter.splice(0);
    if (index === -1) {
      this.props.data.variables.attributesFilter.push(key);
    } else {
      this.props.data.variables.attributesFilter.splice(index, 1);
    }
    this.setState({
      loading: true
    });

    this.timer = +new Date();
    setTimeout(() => {
      if (this.timer + WAIT_FOR_INPUT - 5 < +new Date()) {
        this.setState({
          loading: false
        });
        this.props.data.refetch({
          attributesFilter: this.props.data.variables.attributesFilter
        });
      }
    }, WAIT_FOR_INPUT);
  };

  updatePriceFilter = (minPrice, maxPrice) => {
    this.props.data.refetch({
      minPrice: parseFloat(minPrice) || null,
      maxPrice: parseFloat(maxPrice) || null
    });
  };

  persistStateInUrl () {
    const {attributesFilter, count, maxPrice, minPrice, sortBy} = this.props.data.variables;
    let urlParams = {};
    if (minPrice) {
      urlParams['minPrice'] = minPrice;
    }
    if (maxPrice) {
      urlParams['maxPrice'] = maxPrice;
    }
    if (count > this.props.PAGINATE_BY) {
      urlParams['count'] = count;
    }
    if (sortBy) {
      urlParams['sortBy'] = convertSortByFromObject(sortBy);
    }
    attributesFilter.forEach(filter => {
      const [attributeName, valueSlug] = filter.split(':');
      if (attributeName in urlParams) {
        urlParams[attributeName].push(valueSlug);
      } else {
        urlParams[attributeName] = [valueSlug];
      }
    });
    const url = Object.keys(urlParams).length ? '?' + queryString.stringify(urlParams) : location.href.split('?')[0];
    history.pushState({}, null, url);
  }

  componentDidUpdate () {
    // Persist current state of apollo variables as query string. Current
    // variables are available in props after component rerenders, so it has to
    // be called inside componentDidUpdate method.
    this.persistStateInUrl();
  }

  render () {
    const attributes = this.props.data.attributes;
    const category = this.props.data.category;
    const ancestors = category.ancestors.edges;
    const products = this.props.data.products;
    const variables = this.props.data.variables;
    const pendingVariables = {};
    const {filtersMenu} = this.state;

    let sortBy = '';
    if (variables.sortBy) {
      sortBy = convertSortByFromObject(variables.sortBy);
    }

    return (
      <div className="category-page">
        <div className="category-top">
          <div className="row">
            <div className="col-md-7">
              <ul className="breadcrumbs list-unstyled d-none d-md-block">
                <li><a href="/">{pgettext('Main navigation item', 'Home')}</a></li>
                {ancestors && (ancestors.map((node) => {
                  let ancestor = node.node;
                  return (
                    <li key={ancestor.id}><a href={ancestor.url}>{ancestor.name}</a></li>
                  );
                }))}
                <li><a href={category.url}>{category.name}</a></li>
              </ul>
            </div>
            <div className="col-md-5">
              <div className="row">
                <div className="col-6 col-md-2 col-lg-6 filters-menu">
                  <span className="filters-menu__label d-sm-none"
                    onClick={() => this.toggleMenu(filtersMenu)}>{pgettext('Category page filters', 'Filters')}</span>
                  {(variables.attributesFilter.length || variables.minPrice || variables.maxPrice) && (
                    <span className="filters-menu__icon d-sm-none"></span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="row">
          <div className="col-md-4 col-lg-3">
            {filtersMenu && (
              <div className="product-filters">
                <ProductFilters
                  attributes={attributes}
                  checkedAttributes={variables.attributesFilter}
                  onFilterChanged={this.updateAttributesFilter}
                />
                <PriceFilter
                  onFilterChanged={this.updatePriceFilter}
                  onFilterClear={this.clearFilters}
                  maxPrice={variables.maxPrice}
                  minPrice={variables.minPrice}
                />
              </div>
            )}
          </div>
          <div className="col-md-8 col-lg-9 category-list">
            <div className="product-list__header">
              <div className="product-list__header__title">
                <h1>
                  <strong>{category.name}</strong>
                </h1>
              </div>
              <hr />
              <div>
                <SortBy sortedValue={sortBy} setSorting={this.setSorting}/>
              </div>
            </div>
            <div>
              <ProductList
                onLoadMore={this.incrementProductsCount}
                products={products}
                updating={pendingVariables}
                loading={this.props.data.loading || this.state.loading}
              />
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default CategoryPage;