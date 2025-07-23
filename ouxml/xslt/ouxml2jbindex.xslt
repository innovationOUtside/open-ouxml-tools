<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:exsl="http://exslt.org/common"
    xmlns:str="http://exslt.org/strings" extension-element-prefixes="exsl">
    
    
    <!-- OU-XML tag descriptions at: https://learn3.open.ac.uk/mod/oucontent/view.php?id=124345 -->

    <!-- xmlns:functx="http://www.functx.com" -->

    <!-- Strip out any whitespace used to style layout of XML doc we're processing -->
    <xsl:strip-space elements="*"/>

    <!-- Defining a parameter means we can pass values in -->
    <xsl:param name="filestub">test</xsl:param>

    <xsl:output method="text" />
    
    <xsl:template match="/">
        <exsl:document method="html" href="index.md">
            <xsl:apply-templates/>
        </exsl:document>
    </xsl:template>
    
    <!-- OU-XML things -->

    <xsl:template match="Item">
        <!-- metadata? Or directory path? OR Readme in directory? Or contents list? -->
        <!-- <xsl:value-of select="@Module"/> - <xsl:value-of select="CourseTitle"/> -->
        
        <xsl:text># </xsl:text><xsl:value-of select="CourseTitle"/>
        <xsl:text>&#xa;&#xa;</xsl:text>
        <xsl:apply-templates select="//GeneralInfo"/>
        <xsl:apply-templates select="//Rights"/>
    </xsl:template>

    <xsl:template match="Paragraph">
        <xsl:text>&#xa;</xsl:text>
        <xsl:apply-templates select="*|text()" />
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="b">
        <xsl:text>__</xsl:text>
        <xsl:apply-templates select="*|text()" />
        <xsl:text>__</xsl:text>
    </xsl:template>


</xsl:stylesheet>