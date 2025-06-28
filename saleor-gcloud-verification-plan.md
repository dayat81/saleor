# Saleor Google Cloud Deployment Verification Plan

## Overview
This plan outlines the steps to verify our Saleor deployment on Google Cloud Platform, ensuring all core e-commerce functionality is working properly.

## Current Deployment Status
- **Cloud Run Service**: `saleor-app` at https://saleor-app-hvodeun2nq-uc.a.run.app
- **Database**: Cloud SQL PostgreSQL 15 (`saleor-db-demo`)
- **Region**: us-central1
- **Missing**: Redis instance for caching/task queue

## Verification Steps

### 1. Basic Connectivity Tests
- [ ] Verify main application URL responds
- [ ] Check health/status endpoints
- [ ] Test GraphQL Playground access at `/graphql/`
- [ ] Verify database connectivity

### 2. GraphQL API Verification
#### Core Storefront APIs (Public)
- [ ] **Products Query**: Fetch product catalog
  ```graphql
  query {
    products(first: 10) {
      edges {
        node {
          id
          name
          slug
          description
        }
      }
    }
  }
  ```

- [ ] **Product Details**: Get specific product with variants
  ```graphql
  query ProductDetails($id: ID!) {
    product(id: $id) {
      id
      name
      variants {
        id
        name
        pricing {
          price {
            gross {
              amount
              currency
            }
          }
        }
      }
    }
  }
  ```

#### Checkout Flow Testing
- [ ] **Create Checkout**: Initialize new checkout session
- [ ] **Add Products**: Add items to checkout
- [ ] **Set Addresses**: Configure shipping/billing addresses
- [ ] **Select Shipping**: Choose shipping method
- [ ] **Complete Order**: Finalize checkout process

#### Admin APIs (Authenticated)
- [ ] **User Authentication**: Test admin login
- [ ] **Order Management**: Create and manage orders
- [ ] **Product Management**: CRUD operations on products
- [ ] **Inventory Management**: Stock level operations

### 3. Performance & Scalability Tests
- [ ] **Response Times**: Measure API response latency
- [ ] **Concurrent Requests**: Test multiple simultaneous requests
- [ ] **Database Performance**: Monitor query execution times
- [ ] **Memory Usage**: Check Cloud Run memory consumption

### 4. Integration Tests
- [ ] **Webhook Functionality**: Test event notifications (if configured)
- [ ] **Payment Processing**: Verify payment gateway integration
- [ ] **Email Services**: Test order confirmation emails
- [ ] **File Storage**: Verify media/image uploads

### 5. Security Verification
- [ ] **CORS Configuration**: Test cross-origin requests
- [ ] **Authentication**: Verify JWT token handling
- [ ] **Rate Limiting**: Test API rate limits
- [ ] **HTTPS**: Confirm SSL certificate validity

### 6. Data Integrity Tests
- [ ] **Sample Data**: Verify populated database has expected data
- [ ] **Data Relationships**: Test foreign key constraints
- [ ] **Migration Status**: Confirm all migrations applied
- [ ] **Admin User**: Test admin@example.com login

## Testing Tools & Commands

### GraphQL Testing
```bash
# Test GraphQL endpoint
curl -X POST https://saleor-app-hvodeun2nq-uc.a.run.app/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ shop { name } }"}'
```

### Health Check
```bash
# Basic connectivity test
curl -I https://saleor-app-hvodeun2nq-uc.a.run.app/
```

### Database Connection Test
```bash
# Connect to Cloud SQL instance
gcloud sql connect saleor-db-demo --user=postgres
```

## Expected Outcomes

### Success Criteria
- [ ] GraphQL Playground accessible and functional
- [ ] All core API queries return valid responses
- [ ] Checkout flow completes successfully
- [ ] Admin interface accessible with proper authentication
- [ ] Database queries execute without errors
- [ ] Response times under acceptable thresholds

### Common Issues to Check
- [ ] Database connection timeouts
- [ ] Missing environment variables
- [ ] Incomplete migrations
- [ ] CORS configuration errors
- [ ] Authentication token issues
- [ ] Missing static file serving

## Monitoring & Logging
- [ ] Check Cloud Run logs for errors
- [ ] Monitor Cloud SQL performance metrics
- [ ] Review application-level logging
- [ ] Set up alerting for critical failures

## Next Steps After Verification
1. **If tests pass**: Document working configuration
2. **If tests fail**: Investigate and fix issues
3. **Production readiness**: Add Redis, configure monitoring
4. **Performance tuning**: Optimize based on test results
5. **Security hardening**: Implement additional security measures

## Notes
- This deployment appears to be a development setup (db-f1-micro tier)
- Consider adding Redis for production workloads
- Separate worker services may be needed for background tasks
- Review scaling requirements based on expected traffic