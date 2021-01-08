"""The schema.org Person model.

For reference see schema.org: https://schema.org/Person
"""

from dataclasses import dataclass
from . import Thing

@dataclass
class Person(Thing):
    """
    The schema.org Person model

    Attributes
    ----------
    additionalName
        Text
        An additional name for a Person, can be used for a middle name.
    address
        PostalAddress or Text
        Physical address of the item.
    affiliation
        Organization
        An organization that this person is affiliated with. For example, a
        school/university, a club, or a team.
    alumniOf
        EducationalOrganization or Organization
        An organization that the person is an alumni of.
        Inverse property: alumni.
    award
        Text
        An award won by or for this item. Supersedes awards.
    birthDate
        Date
        Date of birth.
    birthPlace
        Place
        The place where the person was born.
    brand
        Brand or Organization
        The brand(s) associated with a product or service, or the brand(s)
        maintained by an organization or business person.
    callSign
        Text
        A callsign, as used in broadcasting and radio communications to
        identify people, radio and TV stations, or vehicles.
    children
        Person
        A child of the person.
    colleague
        Person or URL
        A colleague of the person. Supersedes colleagues.
    contactPoint
        ContactPoint
        A contact point for a person or organization. Supersedes contactPoints.
    deathDate
        Date
        Date of death.
    deathPlace
        Place
        The place where the person died.
    duns
        Text
        The Dun & Bradstreet DUNS number for identifying an organization or
        business person.
    email
        Text
        Email address.
    familyName
        Text
        Family name. In the U.S., the last name of an Person. This can be used
        along with givenName instead of the name property.
    faxNumber
        Text
        The fax number.
    follows
        Person
        The most generic uni-directional social relation.
    funder
        Organization or Person
        A person or organization that supports (sponsors) something through
        some kind of financial contribution.
    gender
        GenderType or Text
        Gender of something, typically a Person, but possibly also fictional
        characters, animals, etc. While http://schema.org/Male and
        http://schema.org/Female may be used, text strings are also acceptable
        for people who do not identify as a binary gender. The gender property
        can also be used in an extended sense to cover e.g. the gender of
        sports teams. As with the gender of individuals, we do not try to
        enumerate all possibilities. A mixed-gender SportsTeam can be indicated
        with a text value of "Mixed".
    givenName
        Text
        Given name. In the U.S., the first name of a Person. This can be used
        along with familyName instead of the name property.
    globalLocationNumber
        Text
        The Global Location Number (GLN, sometimes also referred to as
        International Location Number or ILN) of the respective organization,
        person, or place. The GLN is a 13-digit number used to identify parties
        and physical locations.
    hasCredential
        EducationalOccupationalCredential
        A credential awarded to the Person or Organization.
    hasOccupation
        Occupation
        The Person's occupation. For past professions, use Role for expressing
        dates.
    hasOfferCatalog
        OfferCatalog
        Indicates an OfferCatalog listing for this Organization, Person, or
        Service.
    hasPOS
        Place
        Points-of-Sales operated by the organization or person.
    height
        Distance or QuantitativeValue
        The height of the item.
    homeLocation
        ContactPoint or Place
        A contact location for a person's residence.
    honorificPrefix
        Text
        An honorific prefix preceding a Person's name such as Dr/Mrs/Mr.
    honorificSuffix
        Text
        An honorific suffix preceding a Person's name such as M.D. /PhD/MSCSW.
    interactionStatistic
        InteractionCounter
        The number of interactions for the CreativeWork using the WebSite or
        SoftwareApplication. The most specific child type of InteractionCounter
        should be used. Supersedes interactionCount.
    isicV4
        Text
        The International Standard of Industrial Classification of All Economic
        Activities (ISIC), Revision 4 code for a particular organization,
        business person, or place.
    jobTitle
        DefinedTerm or Text
        The job title of the person (for example, Financial Manager).
    knows
        Person
        The most generic bi-directional social/work relation.
    knowsAbout
        Text or Thing or URL
        Of a Person, and less typically of an Organization, to indicate a topic
        that is known about - suggesting possible expertise but not implying
        it. We do not distinguish skill levels here, or relate this to
        educational content, events, objectives or JobPosting descriptions.
    knowsLanguage
        Language or Text
        Of a Person, and less typically of an Organization, to indicate a known
        language. We do not distinguish skill levels or reading/writing/
        speaking/signing here. Use language codes from the IETF BCP 47
        standard.
    makesOffer
        Offer
        A pointer to products or services offered by the organization or
        person.
        Inverse property: offeredBy.
    memberOf
        Organization or ProgramMembership
        An Organization (or ProgramMembership) to which this Person or
        Organization belongs.
        Inverse property: member.
    naics
        Text
        The North American Industry Classification System (NAICS) code for a
        particular organization or business person.
    nationality
        Country
        Nationality of the person.
    netWorth
        MonetaryAmount or PriceSpecification
        The total financial value of the person as calculated by subtracting
        assets from liabilities.
    owns
        OwnershipInfo or Product
        Products owned by the organization or person.
    parent
        Person
        A parent of this person. Supersedes parents.
    performerIn
        Event
        Event that this person is a performer or participant in.
    publishingPrinciples
        CreativeWork or URL
        The publishingPrinciples property indicates (typically via URL) a
        document describing the editorial principles of an Organization (or
        individual e.g. a Person writing a blog) that relate to their
        activities as a publisher, e.g. ethics or diversity policies. When
        applied to a CreativeWork (e.g. NewsArticle) the principles are those
        of the party primarily responsible for the creation of the
        CreativeWork.

        While such policies are most typically expressed in natural language,
        sometimes related information (e.g. indicating a funder) can be
        expressed using schema.org terminology.
    relatedTo
        Person
        The most generic familial relation.
    seeks
        Demand
        A pointer to products or services sought by the organization or person
        (demand).
    sibling
        Person
        A sibling of the person. Supersedes siblings.
    sponsor
        Organization or Person
        A person or organization that supports a thing through a pledge,
        promise, or financial contribution. e.g. a sponsor of a Medical Study
        or a corporate sponsor of an event.
    spouse
        Person
        The person's spouse.
    taxID
        Text
        The Tax / Fiscal ID of the organization or person, e.g. the TIN in the
        US or the CIF/NIF in Spain.
    telephone
        Text
        The telephone number.
    vatID
        Text
        The Value-added Tax ID of the organization or person.
    weight
        QuantitativeValue
        The weight of the product or person.
    workLocation
        ContactPoint or Place
        A contact location for a person's place of work.
    worksFor
        Organization
        Organizations that the person works for.

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

    additionalName: str = None
    address = None
    affiliation = None
    alumniOf = None
    award: str = None
    birthDate = None
    birthPlace = None
    brand = None
    callSign: str = None
    children = None
    colleague = None
    contactPoint = None
    deathDate = None
    deathPlace = None
    duns: str = None
    email: str = None
    familyName: str = None
    faxNumber: str = None
    follows = None
    funder = None
    gender = None
    givenName: str = None
    globalLocationNumber: str = None
    hasCredential = None
    hasOccupation = None
    hasOfferCatalog = None
    hasPOS = None
    height = None
    homeLocation = None
    honorificPrefix: str = None
    honorificSuffix: str = None
    interactionStatistic = None
    isicV4: str = None
    jobTitle = None
    knows = None
    knowsAbout = None
    knowsLanguage = None
    makesOffer = None
    memberOf = None
    naics: str = None
    nationality = None
    netWorth = None
    owns = None
    parent = None
    performerIn = None
    publishingPrinciples = None
    relatedTo = None
    seeks = None
    sibling = None
    sponsor = None
    spouse = None
    taxID: str = None
    telephone: str = None
    vatID: str = None
    weight = None
    workLocation = None
    worksFor = None
