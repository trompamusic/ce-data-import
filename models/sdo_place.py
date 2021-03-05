"""The schema.org Place model.

For reference see schema.org: https://schema.org/Place
"""

from dataclasses import dataclass
from . import Thing

@dataclass
class Place(Thing):
    """
    The schema.org Place model

    Attributes
    ----------
    additionalProperty
        PropertyValue
        A property-value pair representing an additional characteristics of the
        entitity, e.g. a product feature or another characteristic for which
        there is no matching property in schema.org.

        Note: Publishers should be aware that applications designed to use
        specific schema.org properties (e.g. http://schema.org/width,
        http://schema.org/color, http://schema.org/gtin13, ...) will typically
        expect such data to be provided using those properties, rather than
        using the generic property/value mechanism.
    address
        PostalAddress or Text
        Physical address of the item.
    aggregateRating
        AggregateRating
        The overall rating, based on a collection of reviews or ratings, of the
        item.
    amenityFeature
        LocationFeatureSpecification
        An amenity feature (e.g. a characteristic or service) of the
        Accommodation. This generic property does not make a statement about
        whether the feature is included in an offer for the main accommodation
        or available at extra costs.
    branchCode
        Text
        A short textual code (also called "store code") that uniquely
        identifies a place of business. The code is typically assigned by the
        parentOrganization and used in structured URLs.

        For example, in the URL http://www.starbucks.co.uk/store-locator/etc/detail/3047
        the code "3047" is a branchCode for a particular branch.
    containedInPlace
        Place
        The basic containment relation between a place and one that contains
        it. Supersedes containedIn.
        Inverse property: containsPlace.
    containsPlace
        Place
        The basic containment relation between a place and another that it
        contains.
        Inverse property: containedInPlace.
    event
        Event
        Upcoming or past event associated with this place, organization, or
        action. Supersedes events.
    faxNumber
        Text
        The fax number.
    geo
        GeoCoordinates or GeoShape
        The geo coordinates of the place.
    geoContains
        GeospatialGeometry or Place
        Represents a relationship between two geometries (or the places they
        represent), relating a containing geometry to a contained geometry. "a
        contains b iff no points of b lie in the exterior of a, and at least
        one point of the interior of b lies in the interior of a". As defined
        in DE-9IM.
    geoCoveredBy
        GeospatialGeometry or Place
        Represents a relationship between two geometries (or the places they
        represent), relating a geometry to another that covers it. As defined
        in DE-9IM.
    geoCovers
        GeospatialGeometry or Place
        Represents a relationship between two geometries (or the places they
        represent), relating a covering geometry to a covered geometry. "Every
        point of b is a point of (the interior or boundary of) a". As defined
        in DE-9IM.
    geoCrosses
        GeospatialGeometry or Place
        Represents a relationship between two geometries (or the places they
        represent), relating a geometry to another that crosses it: "a crosses
        b: they have some but not all interior points in common, and the
        dimension of the intersection is less than that of at least one of
        them". As defined in DE-9IM.
    geoDisjoint
        GeospatialGeometry or Place
        Represents spatial relations in which two geometries (or the places
        they represent) are topologically disjoint: they have no point in
        common. They form a set of disconnected geometries." (a symmetric
        relationship, as defined in DE-9IM)
    geoEquals
        GeospatialGeometry or Place
        Represents spatial relations in which two geometries (or the places
        they represent) are topologically equal, as defined in DE-9IM. "Two
        geometries are topologically equal if their interiors intersect and no
        part of the interior or boundary of one geometry intersects the
        exterior of the other" (a symmetric relationship)
    geoIntersects
        GeospatialGeometry or Place
        Represents spatial relations in which two geometries (or the places
        they represent) have at least one point in common. As defined in
        DE-9IM.
    geoOverlaps
        GeospatialGeometry or Place
        Represents a relationship between two geometries (or the places they
        represent), relating a geometry to another that geospatially overlaps
        it, i.e. they have some but not all points in common. As defined in
        DE-9IM.
    geoTouches
        GeospatialGeometry or Place
        Represents spatial relations in which two geometries (or the places
        they represent) touch: they have at least one boundary point in common,
        but no interior points." (a symmetric relationship, as defined in DE-9IM)
    geoWithin
        GeospatialGeometry or Place
        Represents a relationship between two geometries (or the places they
        represent), relating a geometry to one that contains it, i.e. it is
        inside (i.e. within) its interior. As defined in DE-9IM.
    globalLocationNumber
        Text
        The Global Location Number (GLN, sometimes also referred to as
        International Location Number or ILN) of the respective organization,
        person, or place. The GLN is a 13-digit number used to identify parties
        and physical locations.
    hasMap
        Map or URL
        A URL to a map of the place. Supersedes map, maps.
    isAccessibleForFree
        Boolean
        A flag to signal that the item, event, or place is accessible for free.
        Supersedes free.
    isicV4
        Text
        The International Standard of Industrial Classification of All Economic
        Activities (ISIC), Revision 4 code for a particular organization,
        business person, or place.
    latitude
        Number or Text
        The latitude of a location. For example 37.42242 (WGS 84).
    logo
        ImageObject or URL
        An associated logo.
    longitude
        Number or Text
        The longitude of a location. For example -122.08585 (WGS 84).
    maximumAttendeeCapacity
        Integer
        The total number of individuals that may attend an event or venue.
    openingHoursSpecification
        OpeningHoursSpecification
        The opening hours of a certain place.
    photo
        ImageObject or Photograph
        A photograph of this place. Supersedes photos.
    publicAccess
        Boolean
        A flag to signal that the Place is open to public visitors. If this
        property is omitted there is no assumed default boolean value
    review
        Review
        A review of the item. Supersedes reviews.
    slogan
        Text
        A slogan or motto associated with the item.
    smokingAllowed
        Boolean
        Indicates whether it is allowed to smoke in the place, e.g. in the
        restaurant, hotel or hotel room.
    specialOpeningHoursSpecification
        OpeningHoursSpecification
        The special opening hours of a certain place.

        Use this to explicitly override general opening hours brought in scope
        by openingHoursSpecification or openingHours.
    telephone
        Text
        The telephone number.

    Attributes derived from Thing
    -----------------------------
    identifier
        PropertyValue or Text or URL
        The identifier property represents any kind of identifier for any kind
        of Thing, such as ISBNs, GTIN codes, UUIDs etc. Schema.org provides
        dedicated properties for representing many of these, either as textual
        strings or as URL (URI) links. See background notes for more details.
    name
        Text
        The name of the item.
    description
        Text
        A description of the item.
    url
        URL
        URL of the item.
    additionalType
        URL
        An additional type for the item, typically used for adding more
        specific types from external vocabularies in microdata syntax. This is
        a relationship between something and a class that the thing is in. In
        RDFa syntax, it is better to use the native RDFa syntax - the 'typeof'
        attribute - for multiple types. Schema.org tools may have only weaker
        understanding of extra types, in particular those defined externally.
    alternateName
        Text
        An alias for the item.
    disambiguatingDescription
        Text
        A sub property of description. A short description of the item used to
        disambiguate from other, similar items. Information from other
        properties (in particular, name) may be necessary for the description
        to be useful for disambiguation.
    image
        ImageObject or URL
        An image of the item. This can be a URL or a fully described
        ImageObject.
    mainEntityOfPage
        CreativeWork or URL
        Indicates a page (or other CreativeWork) for which this thing is the
        main entity being described. See background notes for details.
        Inverse property: mainEntity.
    potentialAction
        Action
        Indicates a potential Action, which describes an idealized action in
        which this thing would play an 'object' role.
    sameAs
        URL
        URL of a reference Web page that unambiguously indicates the item's
        identity. E.g. the URL of the item's Wikipedia page, Wikidata entry, or
        official website.
    subjectOf
        CreativeWork or Event
        A CreativeWork or Event about this Thing. Inverse property: about.
    """

    additionalProperty = None
    address = None
    aggregateRating = None
    amenityFeature = None
    branchCode: str = None
    containedInPlace = None
    containsPlace = None
    event = None
    faxNumber: str = None
    geo = None
    geoContains = None
    geoCoveredBy = None
    geoCovers = None
    geoCrosses = None
    geoDisjoint = None
    geoEquals = None
    geoIntersects = None
    geoOverlaps = None
    geoTouches = None
    geoWithin = None
    globalLocationNumber: str = None
    hasMap = None
    isAccessibleForFree: bool = None
    isicV4: str = None
    latitude = None
    logo = None
    longitude = None
    maximumAttendeeCapacity: int = None
    openingHoursSpecification = None
    photo = None
    publicAccess: bool = None
    review = None
    slogan: str = None
    smokingAllowed: bool = None
    specialOpeningHoursSpecification = None
    telephone: str = None
