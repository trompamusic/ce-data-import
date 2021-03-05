"""The schema.org MusicRecording model.

For reference see schema.org: https://schema.org/MusicRecording
"""

from dataclasses import dataclass

from . import CreativeWork


@dataclass
class MusicRecording(CreativeWork):
    """
    The schema.org MusicRecording model

    Attributes
    ----------
    byArtist
        MusicGroup or Person
        The artist that performed this album or recording.
    duration
        Duration
        The duration of the item (movie, audio recording, event, etc.) in ISO
        8601 date format.
    inAlbum
        MusicAlbum
        The album to which this recording belongs.
    inPlaylist
        MusicPlaylist
        The playlist to which this recording belongs.
    isrcCode
        Text
        The International Standard Recording Code for the recording.
    recordingOf
        MusicComposition
        The composition this track is a recording of.
        Inverse property: recordedAs.

    Attributes derived from CreativeWork
    ------------------------------------
    about
        Thing
        The subject matter of the content.
    accessibilityAPI
        Text
        Indicates that the resource is compatible with the referenced
        accessibility API (WebSchemas wiki lists possible values).
    accessibilityControl
        Text
        Identifies input methods that are sufficient to fully control the
        described resource (WebSchemas wiki lists possible values).
    accessibilityFeature
        Text
        Content features of the resource, such as accessible media,
        alternatives and supported enhancements for accessibility (WebSchemas
        wiki lists possible values).
    accessibilityHazard
        Text
        A characteristic of the described resource that is physiologically
        dangerous to some users. Related to WCAG 2.0 guideline 2.3 (WebSchemas
        wiki lists possible values).
    accountablePerson
        Person
        Specifies the Person that is legally accountable for the CreativeWork.
    aggregateRating
        AggregateRating
        The overall rating, based on a collection of reviews or ratings, of the
        item.
    alternativeHeadline
        Text
        A secondary title of the CreativeWork.
    associatedMedia
        MediaObject
        A media object that encodes this CreativeWork. This property is a
        synonym for encoding.
    audience
        Audience
        An intended audience, i.e. a group for whom something was created.
        Supersedes serviceAudience.
    audio
        AudioObject
        An embedded audio object.
    author
        Organization or Person
        The author of this content or rating. Please note that author is
        special in that HTML 5 provides a special mechanism for indicating
        authorship via the rel tag. That is equivalent to this and may be used
        interchangeably.
    award
        Text
        An award won by or for this item. Supersedes awards.
    character
        Person
        Fictional person connected with a creative work.
    citation
        CreativeWork or Text
        A citation or reference to another creative work, such as another
        publication, web page, scholarly article, etc.
        Inverse property: citedBy.
    citedBy
        CreativeWork or Text
        Another creative work making a citation or reference to this one.
        Inverse property: citation.
    comment
        Comment
        Comments, typically from users.
    commentCount
        Integer
        The number of comments this CreativeWork (e.g. Article, Question or
        Answer) has received. This is most applicable to works published in Web
        sites with commenting system; additional comments may exist elsewhere.
    contentLocation
        Place
        The location depicted or described in the content. For example, the
        location in a photograph or painting.
    contentRating
        Text
        Official rating of a piece of content—for example,'MPAA PG-13'.
    contributor
        Organization or Person
        A secondary contributor to the CreativeWork or Event.
    copyrightHolder
        Organization or Person
        The party holding the legal copyright to the CreativeWork.
    copyrightYear
        Number
        The year during which the claimed copyright for the CreativeWork was
        first asserted.
    creator
        Organization or Person
        The creator/author of this CreativeWork. This is the same as the Author
        property for CreativeWork.
    dateCreated
        Date or DateTime
        The date on which the CreativeWork was created or the item was added to
        a DataFeed.
    dateModified
        Date or DateTime
        The date on which the CreativeWork was most recently modified or when
        the item's entry was modified within a DataFeed.
    datePublished
        Date
        Date of first broadcast/publication.
    discussionUrl
        URL
        A link to the page containing the comments of the CreativeWork.
    editor
        Person
        Specifies the Person who edited the CreativeWork.
    educationalAlignment
        AlignmentObject
        An alignment to an established educational framework.
    educationalUse
        Text
        The purpose of a work in the context of education; for example,
        'assignment', 'group work'.
    encoding
        MediaObject
        A media object that encodes this CreativeWork. This property is a
        synonym for associatedMedia. Supersedes encodings.
        Inverse property: encodesCreativeWork.
    exampleOfWork
        CreativeWork
        A creative work that this work is an example/instance/realization/
        derivation of.
        Inverse property: workExample.
    fileFormat
        Text or URL
        Media type, typically MIME format (see IANA site) of the content e.g.
        application/zip of a SoftwareApplication binary. In cases where a
        CreativeWork has several media type representations, 'encoding' can be
        used to indicate each MediaObject alongside particular fileFormat
        information. Unregistered or niche file formats can be indicated
        instead via the most appropriate URL, e.g. defining Web page or a
        Wikipedia entry.
    funder
        Organization or Person
        A person or organization that supports (sponsors) something through
        some kind of financial contribution.
    genre
        Text or URL
        Genre of the creative work or group.
    hasPart
        CreativeWork
        Indicates a CreativeWork that is (in some sense) a part of this
        CreativeWork.
        Inverse property: isPartOf.
    headline
        Text
        Headline of the article.
    inLanguage
        Language or Text
        The language of the content or performance or used in an action. Please
        use one of the language codes from the IETF BCP 47 standard. See also
        availableLanguage. Supersedes language.
    interactionStatistic
        InteractionCounter
        The number of interactions for the CreativeWork using the WebSite or
        SoftwareApplication. The most specific child type of InteractionCounter
        should be used. Supersedes interactionCount.
    interactivityType
        Text
        The predominant mode of learning supported by the learning resource.
        Acceptable values are 'active', 'expositive', or 'mixed'.
    isAccessibleForFree
        Boolean
        A flag to signal that the publication is accessible for free.
        Supersedes free.
    isBasedOn
        CreativeWork or Product or URL
        A resource that was used in the creation of this resource. This term
        can be repeated for multiple sources. For example,
        http://example.com/great-multiplication-intro.html. Supersedes
        isBasedOnUrl.
        Inverse property: isBasisFor.
    isBasisFor
        CreativeWork
        A resource that used this resource in its creation process. This term
        can be repeated for multiple reuse.
        Inverse property: isBasedOn.
    isFamilyFriendly
        Boolean
        Indicates whether this content is family friendly.
    isPartOf
        CreativeWork
        Indicates a CreativeWork that this CreativeWork is (in some sense) part
        of.
        Inverse property: hasPart.
    keywords
        Text
        Keywords or tags used to describe this content. Multiple entries in a
        keywords list are typically delimited by commas.
    learningResourceType
        Text
        The predominant type or kind characterizing the learning resource. For
        example, 'presentation', 'handout'.
    license
        CreativeWork or URL
        A license document that applies to this content, typically indicated by
        URL.
    locationCreated
        Place
        The location where the CreativeWork was created, which may not be the
        same as the location depicted in the CreativeWork.
    mainEntity
        Thing
        Indicates the primary entity described in some page or other
        CreativeWork.
        Inverse property: mainEntityOfPage.
    material
        Product or Text or URL
        A material that something is made from, e.g. leather, wool, cotton,
        paper.
    mentions
        Thing
        Indicates that the CreativeWork contains a reference to, but is not
        necessarily about a concept.
    offers
        Offer
        An offer to provide this item—for example, an offer to sell a product,
        rent the DVD of a movie, perform a service, or give away tickets to an
        event.
    position
        Integer or Text
        The position of an item in a series or sequence of items.
    producer
        Organization or Person
        The person or organization who produced the work (e.g. music album,
        movie, tv/radio series etc.).
    provider
        Organization or Person
        The service provider, service operator, or service performer; the goods
        producer. Another party (a seller) may offer those services or goods on
        behalf of the provider. A provider may also serve as the seller.
        Supersedes carrier.
    publication
        PublicationEvent
        A publication event associated with the item.
    publisher
        Organization or Person
        The publisher of the creative work.
    publishingPrinciples
        URL
        Link to page describing the editorial principles of the organization
        primarily responsible for the creation of the CreativeWork.
    recordedAt
        Event
        The Event where the CreativeWork was recorded. The CreativeWork may
        capture all or part of the event.
        Inverse property: recordedIn.
    releasedEvent
        PublicationEvent
        The place and time the release was issued, expressed as a
        PublicationEvent.
    review
        Review
        A review of the item. Supersedes reviews.
    schemaVersion
        Text or URL
        Indicates (by URL or string) a particular version of a schema used in
        some CreativeWork. For example, a document could declare a
        schemaVersion using an URL such as http://schema.org/version/2.0/ if
        precise indication of schema version was required by some application.
    sourceOrganization
        Organization
        The Organization on whose behalf the creator was working.
    spatialCoverage
        Place
        The spatialCoverage of a CreativeWork indicates the place(s) which are
        the focus of the content. It is a subproperty of contentLocation
        intended primarily for more technical and detailed materials. For
        example with a Dataset, it indicates areas that the dataset describes:
        a dataset of New York weather would have spatialCoverage which was the
        place: the state of New York. Supersedes spatial.
    sponsor
        Organization or Person
        A person or organization that supports a thing through a pledge,
        promise, or financial contribution. e.g. a sponsor of a Medical Study
        or a corporate sponsor of an event.
    temporalCoverage
        DateTime or Text or URL
        The temporalCoverage of a CreativeWork indicates the period that the
        content applies to, i.e. that it describes, either as a DateTime or as
        a textual string indicating a time period in ISO 8601 time interval
        format. Open date ranges, while not allowed in ISO 8601, can be
        expressed by omitting the corresponding start or end date (range with
        unknown end date : "1998-07-01/", range with unknown start date :
        "/2000-12-31T11:59:59"). In the case of a Dataset the temporalCoverage
        will typically indicate the relevant time period in a precise notation
        (e.g. for a 2011 census dataset, the year 2011 would be written
        "2011/2012"). Other forms of content e.g. ScholarlyArticle, Book,
        TVSeries or TVEpisode may indicate their temporalCoverage in broader
        terms - textually or via well-known URL. Written works such as books
        may sometimes have precise temporal coverage too, e.g. a work set in
        1939 - 1945 can be indicated in ISO 8601 interval format format via
        "1939/1945". Supersedes datasetTimeInterval, temporal.
    text
        Text
        The textual content of this CreativeWork.
    thumbnailUrl
        URL
        A thumbnail image relevant to the Thing.
    timeRequired
        Duration
        Approximate or typical time it takes to work with or through this
        learning resource for the typical intended target audience, e.g.
        'P30M', 'P1H25M'.
    translator
        Organization or Person
        Organization or person who adapts a creative work to different
        languages, regional differences and technical requirements of a target
        market, or that translates during some event.
    typicalAgeRange
        Text
        The typical expected age range, e.g. '7-9', '11-'.
    version
        Number or Text
        The version of the CreativeWork embodied by a specified resource.
    video
        VideoObject
        An embedded video object.
    workExample
        CreativeWork
        Example/instance/realization/derivation of the concept of this creative
        work. eg. The paperback edition, first edition, or eBook.
        Inverse property: exampleOfWork.

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

    byArtist = None
    duration = None
    inAlbum = None
    inPlaylist = None
    isrcCode: str = None
    recordingOf = None
