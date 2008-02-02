from StringIO import StringIO

from zope.app.component.hooks import setSite, setHooks
from zope.component import getSiteManager
from zope.component import getUtility
from zope.component import queryUtility
from zope.interface import Interface

from xml.dom.minidom import parseString

from Products.GenericSetup.testing import DummySetupEnviron

from plone.portlets.interfaces import IPortletType

from plone.app.portlets.exportimport.portlets import PortletsXMLAdapter
from plone.app.portlets.interfaces import IColumn
from plone.app.portlets.interfaces import IDashboard
from plone.app.portlets.tests.base import PortletsTestCase

class TestImportPortlets(PortletsTestCase):

    def afterSetUp(self):
        setHooks()
        setSite(self.portal)
        sm = getSiteManager(self.portal)
        self.importer = PortletsXMLAdapter(sm, DummySetupEnviron())
    
    def test_removePortlet(self):
        self.failUnless(queryUtility(IPortletType,
          name='portlets.Calendar') is not None)
        self.assertEqual(True,
          self.importer._removePortlet('portlets.Calendar'))
        self.failUnless(queryUtility(IPortletType,
          name='portlets.Calendar') is None)
        self.assertEqual(False, self.importer._removePortlet('foo'))
    
    def test_checkBasicPortletNodeErrors(self):
        node = parseString(_XML_INVALID_EXTEND_AND_PURGE).documentElement
        self.assertEqual(
          True, self.importer._checkBasicPortletNodeErrors(node,
          ['portlets.Exists'])
          ) 
        node = parseString(_XML_INVALID_EXTEND_NONEXISTS).documentElement
        self.assertEqual(
          True, self.importer._checkBasicPortletNodeErrors(node,
          ['portlets.Exists'])
          )
        node = parseString(_XML_INVALID_ADD_EXISTING).documentElement
        self.assertEqual(
          True, self.importer._checkBasicPortletNodeErrors(node,
          ['portlets.Exists'])
          )
        node = parseString(_XML_EXTEND_EXISTING).documentElement
        self.assertEqual(
          False, self.importer._checkBasicPortletNodeErrors(node,
          ['portlets.Exists'])
          )        
    
    def test_modifyForList(self):
        node = parseString(_XML_SWITCH_COLUMNS).documentElement
        self.assertEqual([IColumn],
          self.importer._modifyForList(node, [IDashboard]))
        node = parseString(_XML_BBB_INTERFACE).documentElement
        self.assertEqual([IColumn],
          self.importer._modifyForList(node, []))
    
    def test_initPortletNode_duplicateInterfaces(self): 
        node = parseString(_XML_DUPLICATE_INTERFACES).documentElement 
        self.importer._initPortletNode(node) 
        portlet = queryUtility(IPortletType, name="portlets.New") 
        self.failUnless(portlet is not None) 
        self.assertEqual([IColumn], portlet.for_) 
    
    def test_initPortletNode_basic(self):
        node = parseString(_XML_BASIC).documentElement
        self.importer._initPortletNode(node)
        portlet = queryUtility(IPortletType, name="portlets.New")
        self.failUnless(portlet is not None)
        self.assertEqual('Foo', portlet.title)
        self.assertEqual('Bar', portlet.description)
        self.assertEqual([IColumn], portlet.for_)
    
    def test_initPortletNode_multipleInterfaces(self):
        node = parseString(_XML_MULTIPLE_INTERFACES).documentElement
        self.importer._initPortletNode(node)
        portlet = queryUtility(IPortletType, name="portlets.New")
        self.failUnless(portlet is not None)
        self.assertEqual([IColumn, IDashboard], portlet.for_)
    
    def test_initPortletNode_defaultManagerInterface(self):
        node = parseString(_XML_DEFAULT_INTERFACE).documentElement
        self.importer._initPortletNode(node)
        portlet = queryUtility(IPortletType, name="portlets.New")
        self.failUnless(portlet is not None)
        self.assertEqual([Interface], portlet.for_)
    
    def test_initPortletNode_BBBInterface(self):
        node = parseString(_XML_BBB_INTERFACE).documentElement
        self.importer._initPortletNode(node)
        portlet = queryUtility(IPortletType, name="portlets.BBB")
        self.failUnless(portlet is not None)
        self.assertEqual([IColumn], portlet.for_)
    
    def test_initPortletNode_extend(self):
        node = parseString(_XML_EXTENDME_SETUP).documentElement
        self.importer._initPortletNode(node)
        node = parseString(_XML_EXTENDME_EXTENSION).documentElement
        self.importer._initPortletNode(node) 
        portlet = queryUtility(IPortletType, name="portlets.ExtendMe")
        self.failUnless(portlet is not None)
        self.assertEqual([IDashboard], portlet.for_)
        self.assertEqual('Bar', portlet.title)
        self.assertEqual('Bar', portlet.description)
    
    def test_initPortletNode_purge(self):
        node = parseString(_XML_PURGEME_SETUP).documentElement
        self.importer._initPortletNode(node)
        node = parseString(_XML_PURGEME_PURGE).documentElement
        self.importer._initPortletNode(node)
        portlet = queryUtility(IPortletType, name="portlets.PurgeMe")
        self.failUnless(portlet is not None)
        self.assertEqual([IColumn], portlet.for_)
        self.assertEqual('Bar', portlet.title)
        self.assertEqual('Bar', portlet.description)
    
    def test_initPortletNode_remove(self):
        node = parseString(_XML_REMOVEME_SETUP).documentElement
        self.importer._initPortletNode(node)
        portlet = queryUtility(IPortletType, name='portlets.RemoveMe')
        self.failUnless(portlet is not None)
        node = parseString(_XML_REMOVEME_REMOVE).documentElement
        self.importer._initPortletNode(node)
        portlet = queryUtility(IPortletType, name='portlets.RemoveMe')
        self.failUnless(portlet is None)

class TestExportPortlets(PortletsTestCase):

    def afterSetUp(self):
        setHooks()
        setSite(self.portal)
        sm = getSiteManager(self.portal)
        self.importer = self.exporter = \
          PortletsXMLAdapter(sm, DummySetupEnviron())

    def test_extractPortletNode(self):
        node = parseString(_XML_MULTIPLE_INTERFACES).documentElement
        self.importer._initPortletNode(node)
        portlet = getUtility(IPortletType, 'portlets.New')
        node = self.exporter._extractPortletNode('portlets.New', portlet)
        file = StringIO()
        node.writexml(file)
        file.seek(0)
        self.assertEqual("""<portlet title="Foo" addview="portlets.New" description="Foo"><for interface="plone.app.portlets.interfaces.IColumn"/><for interface="plone.app.portlets.interfaces.IDashboard"/></portlet>""", file.read())

    def test_extractPortletNode_defaultManagerInterface(self):
        node = parseString(_XML_EXPLICIT_DEFAULT_INTERFACE).documentElement
        self.importer._initPortletNode(node)
        portlet = getUtility(IPortletType, 'portlets.New')
        node = self.exporter._extractPortletNode('portlets.New', portlet)
        file = StringIO()
        node.writexml(file)
        file.seek(0)
        self.assertEqual("""<portlet title="Foo" addview="portlets.New" description="Foo"/>""", file.read())

class TestHelperMethods(PortletsTestCase):

    def afterSetUp(self):
        setHooks()
        setSite(self.portal)
        sm = getSiteManager(self.portal)
        self.importer = self.exporter = PortletsXMLAdapter(sm,
          DummySetupEnviron())
    
    def test_BBB_for(self):
        self.assertEqual([Interface], self.importer._BBB_for(None))
        self.assertEqual([], self.importer._BBB_for([]))
        self.assertEqual([Interface], self.importer._BBB_for(Interface))
        self.assertEqual([Interface], self.importer._BBB_for([Interface]))

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestImportPortlets))
    suite.addTest(makeSuite(TestExportPortlets))
    suite.addTest(makeSuite(TestHelperMethods))
    return suite

_XML_INVALID_EXTEND_AND_PURGE = """<?xml version="1.0"?>
<portlet addview="portlets.Exists" extend="" purge="" />
"""

_XML_INVALID_EXTEND_NONEXISTS = """<?xml version="1.0"?>
<portlet addview="portlets.NonExists" extend="" />
"""

_XML_INVALID_ADD_EXISTING = """<?xml version="1.0"?>
<portlet addview="portlets.Exists" title="Foo" description="Foo" />
"""

_XML_EXTEND_EXISTING = """<?xml version="1.0"?>
<portlet addview="portlets.Exists" extend="" />
"""

_XML_SWITCH_COLUMNS = """<?xml version="1.0"?>
<portlet addview="portlets.Exists" extend="">
  <for interface="plone.app.portlets.interfaces.IColumn" />
  <for interface="plone.app.portlets.interfaces.IDashboard" remove ="" />
</portlet>
"""

_XML_BASIC = """<?xml version="1.0"?>
<portlet addview="portlets.New" title="Foo" description="Bar">
  <for interface="plone.app.portlets.interfaces.IColumn" />
</portlet>
"""

_XML_MULTIPLE_INTERFACES = """<?xml version="1.0"?>
<portlet addview="portlets.New" title="Foo" description="Foo">
  <for interface="plone.app.portlets.interfaces.IColumn" />
  <for interface="plone.app.portlets.interfaces.IDashboard" />
</portlet>
"""

_XML_DUPLICATE_INTERFACES = """<?xml version="1.0"?> 
<portlet addview="portlets.New" title="Foo" description="Foo"> 
  <for interface="plone.app.portlets.interfaces.IColumn" /> 
  <for interface="plone.app.portlets.interfaces.IColumn" /> 
</portlet> 
"""

_XML_DEFAULT_INTERFACE = """<?xml version="1.0"?>
<portlet addview="portlets.New" title="Foo" description="Foo" />
"""

_XML_EXTENDME_SETUP = """<?xml version="1.0"?>
<portlet addview="portlets.ExtendMe" title="Foo" description="Foo">
  <for interface="plone.app.portlets.interfaces.IColumn" />
</portlet>
"""

_XML_EXTENDME_EXTENSION = """<?xml version="1.0"?>
<portlet addview="portlets.ExtendMe" extend="" title="Bar" description="Bar">
  <for interface="plone.app.portlets.interfaces.IColumn" remove="" />
  <for interface="plone.app.portlets.interfaces.IDashboard" />
</portlet>
"""

_XML_PURGEME_SETUP = """<?xml version="1.0"?>
<portlet addview="portlets.PurgeMe" title="Foo" description="Foo">
  <for interface="plone.app.portlets.interfaces.IDashboard" />
</portlet>
"""

_XML_PURGEME_PURGE = """<?xml version="1.0"?>
<portlet addview="portlets.PurgeMe" purge="" title="Bar" description="Bar">
  <for interface="plone.app.portlets.interfaces.IColumn" />
</portlet>
"""

_XML_REMOVEME_SETUP = """<?xml version="1.0"?>
<portlet addview="portlets.RemoveMe" title="Foo" description="Foo" />
"""

_XML_REMOVEME_REMOVE = """<?xml version="1.0"?>
<portlet addview="portlets.RemoveMe" remove="" />
"""

_XML_EXPLICIT_DEFAULT_INTERFACE = """<?xml version="1.0"?>
<portlet addview="portlets.New" title="Foo" description="Foo">
  <for interface="zope.interface.Interface" />
</portlet>
"""

_XML_BBB_INTERFACE = """<?xml version="1.0"?>
<portlet addview="portlets.BBB" title="Foo" description="Foo" for="plone.app.portlets.interfaces.IColumn" />
"""
