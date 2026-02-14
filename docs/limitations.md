System Limitations
Overview
This document outlines the current constraints, known limitations, and boundaries of the system. Understanding these limitations is crucial for proper system usage, expectation management, and future improvement planning.
Technical Limitations
Performance Constraints
Request Throughput

Maximum Concurrent Requests: 10,000 requests/second
Peak Capacity: 15,000 requests/second (with auto-scaling)
Burst Handling: 20,000 requests/second for up to 30 seconds
Degradation: Performance degrades beyond 85% capacity
Impact: Response time increases from 200ms to 2s+ under heavy load

Response Time

Target P50: < 200ms
Target P95: < 500ms
Target P99: < 1000ms
Actual P99: Can reach 3000ms during peak hours
Timeout: Hard timeout at 30 seconds

Database Constraints

Connection Pool Size: 100 connections per instance
Query Timeout: 10 seconds
Maximum Result Set: 10,000 rows per query
Transaction Duration: Maximum 30 seconds
Write Throughput: ~5,000 writes/second before replication lag

Storage Limitations
Data Storage

Maximum File Size: 100MB per upload
Total Storage per User: 10GB (free tier), 1TB (premium tier)
Database Row Limit: 100 million rows per table before partitioning required
Object Storage: No hard limit, but costs increase significantly above 10TB
Backup Retention: 30 days for automated backups