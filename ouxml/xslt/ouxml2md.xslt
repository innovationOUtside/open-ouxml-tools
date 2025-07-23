<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:exsl="http://exslt.org/common" xmlns:str="http://exslt.org/strings" extension-element-prefixes="exsl">

    <!-- OU-XML tag descriptions at: https://learn3.open.ac.uk/mod/oucontent/view.php?id=124345 -->

    <!-- xmlns:functx="http://www.functx.com" -->

    <!-- Strip out any whitespace used to style layout of XML doc we're processing -->
    <xsl:strip-space elements="*" />

    <!-- Defining a parameter means we can pass values in -->
    <xsl:param name="filestub">test</xsl:param>

    <xsl:output method="text" />

    <!-- for escaping underscore so as not to clobber markdown,
         need something like:
        <xsl:value-of select="str:replace(string, search, replace)" />
        such as:
        <xsl:value-of select="str:replace(text(), '_', '\_')" />
        Or we could be really hacky and replace everything in the original XML prior to XSLT?
    -->

    <xsl:template match="/">
        <xsl:apply-templates />
    </xsl:template>

    <!-- some common HTMLy things... -->

    <xsl:template match="a">
        <xsl:text>[</xsl:text>
        <xsl:apply-templates select="node()|text()" />
        <xsl:text>](</xsl:text>
        <xsl:value-of select="@href" />
        <xsl:text>)</xsl:text>
    </xsl:template>

    <xsl:template match="i">
        <xsl:text>*</xsl:text>
        <xsl:apply-templates />
        <xsl:text>*</xsl:text>
    </xsl:template>

    <xsl:template match="b">
        <xsl:text>__</xsl:text>
        <xsl:apply-templates />
        <xsl:text>__</xsl:text>
    </xsl:template>

 <!-- Strip whitespace in the emphasis tags-->
  <xsl:template match="b/text()">
    <xsl:value-of select="normalize-space(.)"/>
  </xsl:template>
  <xsl:template match="i/text()">
    <xsl:value-of select="normalize-space(.)"/>
  </xsl:template>

    <xsl:template match="Paragraph/br">
        <xsl:text>&#xa;&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="br">
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>


    <!-- some OU-XML alternatives to HTMLy things... -->

    <!-- If the parent is a ListItem, we need to indent by at least one space.
            This then allows us to have multi-paragraph lists.
        -->
    <xsl:template match="Paragraph">
        <xsl:text>&#xa;</xsl:text>
        <xsl:if test="parent::ListItem">
            <xsl:text></xsl:text>
        </xsl:if>
        <xsl:apply-templates select="*|text()" />
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="Image | Figure/Image">
        <xsl:text>&#xa;&#xa;![</xsl:text>
        <!-- <xsl:value-of select="@alt" /> -->
        <xsl:choose>
            <xsl:when test="../Alternative">
                <xsl:value-of select="../Alternative" />
            </xsl:when>
            <xsl:when test="../Description">
                <xsl:value-of select="../Description" />
            </xsl:when>
            <xsl:otherwise>
                figure
                <xsl:value-of select='str:split(@src, "\\")[last()]' />
                <!--<xsl:value-of select="generate-id()"/> -->
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text>](</xsl:text>
        <!-- <xsl:value-of select="@src" /> -->
        <!-- preprocess the XML to swap in image paths we can resolve? -->
        <!-- Alternatively we could leave the full image path here map on that; more likely to be unique? -->
        <xsl:value-of select='str:split(@src, "\\")[last()]' />
        <xsl:text>)&#xa;</xsl:text>
    </xsl:template>

    <!-- TO DO: does this also have to cope with situation where there is no internal paragraph? -->
    <!-- I'm not sure what semantics of Quote are? eg it's used for SAQ questions? -->
    <xsl:template match="Quote">
        <xsl:text>&#xa;</xsl:text>
        <xsl:comment>
            Quote id=
            <xsl:value-of select="@id" />
        </xsl:comment>
        <xsl:apply-templates />
        <xsl:text>&#xa;&#xa;</xsl:text>
    </xsl:template>

    <!-- TO DO: multiline quotes -->
    <xsl:template match="Quote/Paragraph">
        <xsl:text>&#xa;</xsl:text>
        <xsl:text disable-output-escaping="yes">></xsl:text>
        <xsl:apply-templates />
        <!-- <xsl:value-of select="str:replace(text(), '&#xa;', '&#xa;&gt; ')" /> -->
    </xsl:template>

    <!-- TO DO - nested lists -->
    <xsl:template match="ListItem">
        <!-- <xsl:value-of select="functx:repeat-string('    ', count(ancestor::li))"/> -->
        <xsl:text>&#xa;</xsl:text>
        <xsl:choose>
            <xsl:when test="name(..) = 'NumberedList'">
                <xsl:value-of select="position()" />
                <xsl:text>. </xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>* </xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <!-- <xsl:value-of select="normalize-space(text())" /> -->
        <!-- <xsl:apply-templates select="* except (NumberedList|BulletedList)" /> -->
        <xsl:apply-templates />
        <xsl:text>&#xa;</xsl:text>
        <xsl:apply-templates select="NumberedList|BulletedList" />
    </xsl:template>

    <!-- Original didn't process text() nodes for these to prevent unnecessary whitespace -->
    <xsl:template match="NumberedList|BulletedList">
        <xsl:apply-templates />
    </xsl:template>


    <!-- OU-XML things -->

    <xsl:template match="Item">
        <!-- metadata? Or directory path? OR Readme in directory? Or contents list? -->
        <!-- <xsl:value-of select="@Module"/> - <xsl:value-of select="CourseTitle"/> -->
        <xsl:apply-templates />
    </xsl:template>


    <xsl:template match="Unit">
        <!-- metadata? -->
        <!-- How can we count which unit we are in and use that in setting filenames? -->
        <!-- <xsl:value-of select="UnitTitle"/> -->
        <xsl:param name="filestub" select="position()" />
        <xsl:apply-templates />
    </xsl:template>


    <xsl:template match="LearningOutcomes">
        <xsl:text>&#xa;&#xa;## Learning Outcomes&#xa;&#xa;</xsl:text>
        <xsl:apply-templates />
    </xsl:template>

    <xsl:template match="LearningOutcome">
        <!-- should we get rid of div? Does it break inner md in md doc? -->
        <div class='learningOutcome'>
            <xsl:apply-templates />
        </div>
    </xsl:template>


    <!-- The md output actually starts here with document partitioning -->
    <xsl:template match="Session">
        <!-- Create a new output document for each session -->
        <!-- This requires the directory path to be set, so for new directories
             create directory path stub at the start of the filename and postprocess? -->
        <!-- or to generate a filename (needs tweaking) on _UNIT_SESSION_ -->
        <!-- test_{count(../preceding-sibling::node())}_{position()}.md -->
        <!-- <exsl:document method="html" href="{$filestub}_{count(../preceding-sibling::node())}_{position()}.md"> -->
        <exsl:document method="html" href="{$filestub}_{format-number(count(../preceding-sibling::Unit),'00')}_{format-number(count(preceding-sibling::Session)+1,'00')}.md">
<xsl:text>---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.11.4
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---&#xa;&#xa;</xsl:text>
            <xsl:apply-templates />
        </exsl:document>
    </xsl:template>

    <xsl:template match="Section">
        <xsl:apply-templates />
    </xsl:template>

    <xsl:template match="Session/Title">
        <xsl:text># </xsl:text>
        <xsl:value-of select="." />
        <xsl:text>&#xa;&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="Section/Title">
        <xsl:text>&#xa;&#xa;## </xsl:text>
        <xsl:value-of select="." />
        <xsl:text>&#xa;&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="SubSection/Title">
        <xsl:text>&#xa;&#xa;### </xsl:text>
        <xsl:value-of select="." />
        <xsl:text>&#xa;&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="SubSection">
        <xsl:text>&#xa;&#xa;---&#xa;&#xa;</xsl:text>
        <xsl:apply-templates />
    </xsl:template>

    <xsl:template match="SubSubSection">
        <xsl:text>&#xa;&#xa;---&#xa;&#xa;</xsl:text>
        <xsl:apply-templates />
    </xsl:template>


    <xsl:template match="InternalSection">
        <xsl:text>&#xa;&#xa;---&#xa;&#xa;</xsl:text>
        <xsl:apply-templates />
        <xsl:text>&#xa;&#xa;---&#xa;&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="InternalSection/Heading">
        <xsl:text>&#xa;&#xa;### </xsl:text>
        <xsl:value-of select="." />
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>


    <!-- should we need to add metadata here somewhow? -->
    <xsl:template match="Exercise">
        <xsl:apply-templates />
        <xsl:text>&#xa;&#xa;</xsl:text>
    </xsl:template>


    <xsl:template match="Exercise/Heading">
        <xsl:text>&#xa;&#xa;### </xsl:text>
        <xsl:value-of select="." />
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="Timing">
        <xsl:text>__Timing: </xsl:text>
        <xsl:value-of select="." />
        <xsl:text>__&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="Question">
        <xsl:text>&#xa;&#xa;#### Question&#xa;</xsl:text>
        <xsl:apply-templates />

    </xsl:template>

    <xsl:template match="Activity//Discussion">
        <xsl:text>&#xa;</xsl:text>
        <xsl:comment> #endregion </xsl:comment>
        <xsl:text>&#xa;&#xa;</xsl:text>
        <xsl:comment> #region heading_collapsed=true tags=["style-activity", "precollapse"] </xsl:comment>
        <xsl:text>&#xa;#### Discussion&#xa;</xsl:text>
        <xsl:text>&#xa;Click on the triangle in the sidebar, or run this cell, to reveal my solution.&#xa;</xsl:text>
        <xsl:comment> #endregion </xsl:comment>
        <xsl:text>&#xa;&#xa;</xsl:text>
        <xsl:comment> #region tags=["style-activity"] </xsl:comment>
        <xsl:apply-templates />
        <xsl:comment> #endregion </xsl:comment>
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="Discussion">
        <xsl:text>&#xa;&#xa;#### Discussion&#xa;</xsl:text>
        <xsl:apply-templates />
    </xsl:template>


    <xsl:template match="Answer">
        <xsl:text>&#xa;&#xa;#### Answer&#xa;</xsl:text>
        <xsl:apply-templates />
    </xsl:template>


    <xsl:template match="Figure/Caption/Number">
        <xsl:text>__</xsl:text>
        <xsl:apply-templates />
        <xsl:text>__</xsl:text>
    </xsl:template>


    <xsl:template match="CaseStudy">
        <xsl:text>&#xa;&#xa;----&#xa;&#xa;### Case Study</xsl:text>
        <xsl:apply-templates />
        <xsl:text>&#xa;&#xa;----&#xa;&#xa;</xsl:text>
    </xsl:template>


    <!-- Backmatter is at session level and should create a new doc
         It must contain at least one of:
             <Acknowledgements>, <Appendices>, <Conclusion>, <CourseTeam>,
             <FurtherReading>, <Glossary>, <Index>, <Promotion>, <References>
    -->
    <xsl:template match="Backmatter">
        <exsl:document method="html" href="{$filestub}_{format-number(count(../preceding-sibling::Unit),'00')}_{format-number(count(preceding-sibling::Session)+1,'00')}.md">
            <xsl:text>&#xa;&#xa;# Backmatter&#xa;</xsl:text>
            <xsl:apply-templates />
        </exsl:document>
    </xsl:template>

    <!-- Should this have its own document? Or share one with References? -->
    <xsl:template match="FurtherReading">
        <xsl:text>&#xa;&#xa;## Further Reading&#xa;</xsl:text>
        <xsl:apply-templates />
    </xsl:template>

    <!-- Should this have its own document? Or share one with FurtherReading? -->
    <xsl:template match="References">
        <xsl:text>&#xa;&#xa;## References&#xa;&#xa;</xsl:text>
        <xsl:apply-templates />
    </xsl:template>

    <!-- ReferenceID and ReferenceStyle are further available attributes... -->
    <xsl:template match="Reference">
        <xsl:text>* </xsl:text>
        <xsl:apply-templates select="node()|text()" />
        <xsl:text> [link](</xsl:text>
        <xsl:value-of select="@src" />
        <xsl:text>)</xsl:text>
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>


    <!-- it would be nice to do more with Glossary items? -->
    <xsl:template match="GlossaryTerm">
        <xsl:text>__</xsl:text>
        <xsl:value-of select="." />
        <xsl:text>__</xsl:text>
    </xsl:template>

    <!-- Should we put the glossary in it's own document? Will this trump creating Backmatter doc? -->
    <xsl:template match="Glossary">
        <exsl:document method="html" href="{$filestub}_{format-number(count(../preceding-sibling::Unit),'00')}_glossary.md">
            <xsl:text>&#xa;&#xa;# Glossary&#xa;</xsl:text>
            <xsl:apply-templates />
        </exsl:document>
    </xsl:template>

    <!-- GlossaryItem elements go in the Backmatter/Glossary and
         have Term and Definition components
    -->
    <xsl:template match="GlossaryItem">
        <xsl:apply-templates />
    </xsl:template>

    <xsl:template match="Term">
        <xsl:text>__</xsl:text>
        <xsl:apply-templates />
        <xsl:text>__: </xsl:text>
    </xsl:template>

    <xsl:template match="Definition">
        <xsl:apply-templates />
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>


    <xsl:template match="Box">
        <xsl:text>&#xa;</xsl:text>
        <xsl:comment> #region tags=["style-box", "alert-success"] </xsl:comment>
        <xsl:apply-templates /><xsl:text>&#xa;</xsl:text>
        <xsl:comment> #endregion </xsl:comment>
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="Box/Heading">
        <xsl:text>&#xa;&#xa;### </xsl:text>
        <xsl:value-of select="." />
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>

    <!-- Activity:
        MUST contain contain <Question>
        OPTIONAL: <Heading>, <Timing>, <Multipart> X, <MediaContent>, <Interaction> X, <Answer>, <Discussion>
    -->
    <xsl:template match="Activity">
        <xsl:text>&#xa;</xsl:text>
        <xsl:comment> #region tags=["style-activity"] </xsl:comment><xsl:text>&#xa;</xsl:text>
        <xsl:text>```{admonition} Activity</xsl:text>
        <xsl:apply-templates />
        <xsl:text>&#xa;</xsl:text>
        <xsl:text>```</xsl:text>
        <xsl:text>&#xa;</xsl:text>
        <xsl:comment> #endregion </xsl:comment><xsl:text>&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="Activity/Heading">
        <xsl:text>&#xa;### </xsl:text>
        <xsl:value-of select="." />
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="ComputerUI">
        <xsl:text>`</xsl:text>
        <xsl:apply-templates />
        <xsl:text>`</xsl:text>
    </xsl:template>

    <xsl:template match="ProgramListing">
        <xsl:text>&#xa;&#xa;```python&#xa;</xsl:text>
        <xsl:apply-templates />
        <xsl:text>&#xa;```&#xa;&#xa;</xsl:text>
    </xsl:template>

    <!-- I think this is inline code -->
    <xsl:template match="ComputerCode | b/ComputerCode | ComputerCode/b ">
        <xsl:text>`</xsl:text>
        <xsl:apply-templates />
        <xsl:text>`</xsl:text>
    </xsl:template>

    <xsl:template match="Activity//ComputerDisplay">
        <xsl:text>&#xa;</xsl:text>
        <xsl:comment> #endregion </xsl:comment>
        <xsl:text>&#xa;&#xa;```python tags=["style-activity"]&#xa;</xsl:text>
        <xsl:apply-templates />
        <xsl:text>&#xa;```&#xa;</xsl:text>
        <xsl:text>&#xa;&#xa;</xsl:text>
        <xsl:comment> #region tags=["style-activity"] </xsl:comment>
    </xsl:template>

    <xsl:template match="ComputerDisplay">
        <xsl:text>&#xa;&#xa;```python&#xa;</xsl:text>
        <xsl:apply-templates />
        <xsl:text>&#xa;```&#xa;&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="ComputerDisplay/Paragraph">
        <xsl:text>&#xa;</xsl:text>
        <xsl:apply-templates />
    </xsl:template>

    <xsl:template match="ComputerDisplay/Paragraph/br">
        <xsl:text>&#xa;</xsl:text>
        <xsl:apply-templates />
    </xsl:template>

    <xsl:template match="ComputerDisplay/Paragraph/ComputerCode">
        <xsl:text>&#xa;</xsl:text>
        <xsl:apply-templates />
    </xsl:template>

    <xsl:template match="ComputerDisplay/Paragraph/text()">
        <xsl:value-of select="." disable-output-escaping="yes" />
    </xsl:template>


    <!-- TO DO -->

    <!-- is there a transcript element? -->


    <xsl:template match="SideNote">
        <xsl:text>&#xa;</xsl:text>
        <xsl:comment> #region tags=["style-sidenote", "alert-warning"] </xsl:comment>
        <xsl:apply-templates />
        <xsl:text>&#xa;</xsl:text>
        <xsl:comment> #endregion </xsl:comment>
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="SideNoteParagraph">
        <p>
            <xsl:apply-templates />
        </p>
    </xsl:template>


    <xsl:template match="Tables">
        <xsl:comment>TABLES</xsl:comment>
        <xsl:apply-templates />
        <xsl:comment>ENDTABLES</xsl:comment>
    </xsl:template>

    <xsl:template match="Table">
        <table>
            <xsl:apply-templates />
        </table>
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="TableHead/Number">
        <em>
            <xsl:value-of select="." />
        </em>
    </xsl:template>

    <xsl:template match="TableHead">
        <caption>
            <xsl:apply-templates />
        </caption>
    </xsl:template>

    <xsl:template match="tbody">
        <tbody>
            <xsl:apply-templates />
        </tbody>
    </xsl:template>

    <xsl:template match="tr">
        <tr>
            <xsl:apply-templates />
        </tr>
    </xsl:template>

    <xsl:template match="th">
        <th>
            <xsl:apply-templates />
        </th>
    </xsl:template>

    <xsl:template match="td">
        <td class="highlight_{@highlight}" rowspan="{@rowspan}" colspan="{@colspan}">
            <xsl:apply-templates />
        </td>
    </xsl:template>


    <xsl:template match="Figures">
        <xsl:comment>FIGURES</xsl:comment>
        <xsl:apply-templates />
        <xsl:comment>ENDFIGURES</xsl:comment>
    </xsl:template>

    <xsl:template match="MediaContent">
        <xsl:comment>MEDIACONTENT</xsl:comment>
        <xsl:apply-templates />
        <xsl:comment>ENDMEDIACONTENT</xsl:comment>
    </xsl:template>

    <xsl:template match="MediaContent[@type = 'video']">
        <xsl:comment>MEDIACONTENT</xsl:comment>
        <!-- Stricly this is for media and we should mathc on media type=='video' -->
        <video>
            <xsl:attribute name="width">80%</xsl:attribute>
            <xsl:attribute name="download" />
            <source src='{str:split(@src, "\\")[last()]}' type="video/mp4"></source>
        </video>
        <xsl:apply-templates />
        <xsl:comment>ENDMEDIACONTENT</xsl:comment>
    </xsl:template>

    <xsl:template match="SourceReference">
        <xsl:text>&#xa;Reference: </xsl:text>
        <xsl:apply-templates />
        <xsl:text>&#xa;&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="Transcript">
        <xsl:comment>TRANSCRIPT</xsl:comment>
        <table border="1">
            <tr>
                <td>
                    <xsl:apply-templates />
                </td>
            </tr>
        </table>
        <xsl:comment>ENDTRANSCRIPT</xsl:comment>
    </xsl:template>

    <xsl:template match="Speaker">
        <xsl:text>&#xa;__</xsl:text>
        <xsl:apply-templates />
        <xsl:text>:__ </xsl:text>
    </xsl:template>

    <xsl:template match="Remark">
        <xsl:text>*</xsl:text>
        <xsl:apply-templates />
        <xsl:text>*;&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="Caption">
        <xsl:text>&#xa;&#xa;</xsl:text>
        <xsl:apply-templates />
        <xsl:text>&#xa;&#xa;</xsl:text>
    </xsl:template>


    <xsl:template match="Chemistry">
        <xsl:comment>CHEMISTRY</xsl:comment>
        <xsl:apply-templates />
        <xsl:comment>ENDCHEMISTRY</xsl:comment>
    </xsl:template>

    <xsl:template match="Equation/MathML/math">
        <xsl:text> $$</xsl:text>
        <xsl:value-of select="." />
        <xsl:text> $$ </xsl:text>
    </xsl:template>

    <xsl:template match="Figure">
        <xsl:apply-templates />
    </xsl:template>

    <xsl:template match="InlineFigure/Image | InlineEquation/Image">
        <xsl:text> ![</xsl:text>
        <!-- <xsl:value-of select="@alt" /> -->
        <xsl:choose>
            <xsl:when test="../Alternative">
                <xsl:value-of select="../Alternative" />
            </xsl:when>
            <xsl:otherwise>
                inlinefigure
                <xsl:value-of select='str:split(@src, "\\")[last()]' />
                <!--<xsl:value-of select="generate-id()"/>-->
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text>](</xsl:text>
        <!-- There is a ?display=inline-block arg we could add at the end but this would break image link reconciliation? -->
        <xsl:value-of select='str:split(@src, "\\")[last()]' />
        <xsl:text>) </xsl:text>
    </xsl:template>

    <xsl:template match="Extract">
        <xsl:comment>EXTRACT</xsl:comment>
        <xsl:apply-templates />
        <xsl:comment>ENDEXTRACT</xsl:comment>
    </xsl:template>

    <xsl:template match="Dialogue">
        <xsl:comment>DIALOGUE</xsl:comment>
        <xsl:apply-templates />
        <xsl:comment>ENDDIALOGUE</xsl:comment>
    </xsl:template>

    <xsl:template match="Alternative"></xsl:template>
    <xsl:template match="Description"></xsl:template>

    <xsl:template match="SAQ">
        <xsl:comment>
            SAQ id=
            <xsl:value-of select="@id" />
        </xsl:comment>
        <xsl:apply-templates />
        <xsl:comment>ENDSAQ</xsl:comment>
    </xsl:template>

    <xsl:template match="SAQ/Heading">
        <xsl:text>&#xa;&#xa;### </xsl:text>
        <xsl:value-of select="." />
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>

    <xsl:template match="ITQ">
        <xsl:comment>ITQ</xsl:comment>
        <xsl:apply-templates />
        <xsl:comment>ENDITQ</xsl:comment>
    </xsl:template>


    <xsl:template match="KeyPoints">
        <xsl:comment>KEYPOINTS</xsl:comment>
        <xsl:apply-templates />
        <xsl:comment>ENDKEYPOINTS</xsl:comment>
    </xsl:template>

    <xsl:template match="Summary">
        <xsl:comment>SUMMARY</xsl:comment>
        <xsl:apply-templates />
        <xsl:comment>ENDSUMMARY</xsl:comment>
    </xsl:template>

    <xsl:template match="Reading">
        <xsl:comment>READING</xsl:comment>
        <xsl:apply-templates />
        <xsl:comment>ENDREADING</xsl:comment>
    </xsl:template>


    <xsl:template match="Example">
        <xsl:comment>EXAMPLE</xsl:comment>
        <xsl:apply-templates />
        <xsl:comment>ENDEXAMPLE</xsl:comment>
    </xsl:template>


    <xsl:template match="Verse">
        <xsl:comment>VERSE</xsl:comment>
        <xsl:apply-templates />
        <xsl:comment>ENDVERSE</xsl:comment>
    </xsl:template>

    <xsl:template match="StudyNote">
        <div style='background:lightgreen'>

            <xsl:apply-templates />
        </div>
    </xsl:template>


    <!-- This is here as a warning / catch all for any missed heading types -->
    <xsl:template match="Heading">
        <xsl:comment>
            Heading:
            <xsl:value-of select="." />
        </xsl:comment>
    </xsl:template>


    <!-- how do we handle this? -->
    <xsl:template match="CrossRef">
        <a href="{idref}">
            <xsl:value-of select="." />
        </a>
    </xsl:template>


    <xsl:template match="TeX">
        <xsl:text>$$</xsl:text>
        <xsl:value-of select="." />
        <xsl:text>$$</xsl:text>
    </xsl:template>

    <xsl:template match="sub">
        <sub>
            <xsl:apply-templates />
        </sub>
    </xsl:template>

    <xsl:template match="sup">
        <sup>
            <xsl:apply-templates />
        </sup>
    </xsl:template>

    <xsl:template match="SideNote">
        <xsl:apply-templates />
    </xsl:template>

    <xsl:template match="SideNoteParagraph">
        <!-- TO DO: add a link reference to a popup or footer? -->
    </xsl:template>


    <!-- clear up extraneous whitespace -->
    <!-- This going too far? There whitespace we need around tags... -->
    <!--
    <xsl:template match="text()">
        <xsl:value-of select="normalize-space()"/>
    </xsl:template>
    -->

</xsl:stylesheet>