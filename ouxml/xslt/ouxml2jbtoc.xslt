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
        <exsl:document method="html" href="_toc.yml">
            <xsl:apply-templates/>
        </exsl:document>
    </xsl:template>
    
    <!-- OU-XML things -->

    <xsl:template match="Item">
        <!-- metadata? Or directory path? OR Readme in directory? Or contents list? -->
        <!-- <xsl:value-of select="@Module"/> - <xsl:value-of select="CourseTitle"/> -->
        <xsl:text>format: jb-book&#xa;</xsl:text>
        <xsl:text>root: index&#xa;</xsl:text>
        <xsl:text>parts:&#xa;</xsl:text>
        <xsl:apply-templates/>

    </xsl:template>


    <xsl:template match="Unit">
        <!-- metadata? -->
        <!-- How can we count which unit we are in and use that in setting filenames? -->
        <!-- <xsl:value-of select="UnitTitle"/> -->
        <xsl:param name="filestub" select="position()"/>
        <xsl:text>&#xa;  - caption: "</xsl:text><xsl:value-of select="./UnitTitle" /><xsl:text>"</xsl:text>
       <xsl:text>&#xa;    chapters:</xsl:text>
        <xsl:apply-templates/>
    </xsl:template>
 
    <xsl:template match="Session">
       <xsl:text>&#xa;    - file: </xsl:text><xsl:value-of select="$filestub" /><xsl:text>_</xsl:text><xsl:value-of select="format-number(count(../preceding-sibling::Unit),'00')" /><xsl:text>_</xsl:text><xsl:value-of select="format-number(count(preceding-sibling::Session)+1,'00')" />
    </xsl:template>
    <xsl:template match="text()"/>
</xsl:stylesheet>