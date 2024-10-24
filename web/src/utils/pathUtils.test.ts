import { hasPathDatetime, parsePath } from './pathUtils';

describe('pathUtils', () => {
  describe('parsePath', () => {
    it('should return null for empty path', () => {
      expect(parsePath('')).equals(null);
    });

    describe('zone paths', () => {
      it('should parse basic zone path without timeAverage', () => {
        expect(parsePath('/zone/US-CA')).to.deep.equal({
          type: 'zone',
          zoneId: 'US-CA',
        });
      });

      it('should parse zone path with timeAverage', () => {
        expect(parsePath('/zone/US-CA/hourly')).to.deep.equal({
          type: 'zone',
          zoneId: 'US-CA',
          timeAverage: 'hourly',
        });
      });

      it('should parse zone path with targetDatetime', () => {
        expect(parsePath('/zone/US-CA/hourly/2024-10-20T08:00:00Z')).to.deep.equal({
          type: 'zone',
          zoneId: 'US-CA',
          timeAverage: 'hourly',
          datetime: '2024-10-20T08:00:00Z',
        });
      });

      it('should return null for incomplete zone path', () => {
        expect(parsePath('/zone')).equals(null);
      });
    });

    describe('map paths', () => {
      it('should parse basic map path without timeAverage', () => {
        expect(parsePath('/map')).to.deep.equal({
          type: 'map',
        });
      });

      it('should parse map path with timeAverage', () => {
        expect(parsePath('/map/daily')).to.deep.equal({
          type: 'map',
          timeAverage: 'daily',
        });
      });

      it('should parse map path with targetDatetime', () => {
        expect(parsePath('/map/daily/2024-10-20T08:00:00Z')).to.deep.equal({
          type: 'map',
          timeAverage: 'daily',
          datetime: '2024-10-20T08:00:00Z',
        });
      });
    });

    it('should return null for unknown route type', () => {
      expect(parsePath('/unknown')).equals(null);
    });
  });

  describe('hasPathDatetime', () => {
    describe('zone paths', () => {
      it('should return false for basic zone path', () => {
        expect(hasPathDatetime('/zone/US-CA')).equals(false);
      });

      it('should return false for zone path with only timeAverage', () => {
        expect(hasPathDatetime('/zone/US-CA/hourly')).equals(false);
      });

      it('should return true for zone path with datetime', () => {
        expect(hasPathDatetime('/zone/US-CA/daily/2024-10-20T08:00:00Z')).equals(true);
      });
    });

    describe('map paths', () => {
      it('should return false for basic map path', () => {
        expect(hasPathDatetime('/map/daily')).equals(false);
      });

      it('should return true for map path with datetime', () => {
        expect(hasPathDatetime('/map/2024-10-20T08:00:00Z')).equals(true);
      });
    });

    it('should return true for root path with datetime', () => {
      expect(hasPathDatetime('/2024-10-20T08:00:00Z')).equals(true);
    });

    it('should return false for invalid path', () => {
      expect(hasPathDatetime('/invalid')).equals(false);
    });
  });
});
