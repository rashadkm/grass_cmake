
/****************************************************************************
* MODULE:       R-Tree library 
*              
* AUTHOR(S):    Antonin Guttman - original code
*               Daniel Green (green@superliminal.com) - major clean-up
*                               and implementation of bounding spheres
*               Markus Metz - R*-tree
*               
* PURPOSE:      Multidimensional index
*
* COPYRIGHT:    (C) 2009 by the GRASS Development Team
*
*               This program is free software under the GNU General Public
*               License (>=v2). Read the file COPYING that comes with GRASS
*               for details.
*****************************************************************************/

#include <stdlib.h>
#include <assert.h>
#include "index.h"
#include "card.h"

/* stack used for non-recursive insertion/deletion */
struct stack
{
    struct Node *sn;		/* stack node */
    int branch_id;		/* branch no to follow down */
};

/* 
 * Make a new index, empty.
 * ndims number of dimensions
 * returns pointer to RTree structure
 */
struct RTree *RTreeNewIndex(int ndims)
{
    struct RTree *new_rtree;
    struct Node *n;

    new_rtree = (struct RTree *)malloc(sizeof(struct RTree));

    new_rtree->ndims = ndims;
    new_rtree->nsides = 2 * ndims;

    new_rtree->nodesize = sizeof(struct Node);
    new_rtree->branchsize = sizeof(struct Branch);
    new_rtree->rectsize = sizeof(struct Rect);

    /* nodecard and leafcard can be adjusted, must NOT be larger than MAXCARD */
    new_rtree->nodecard = MAXCARD;
    new_rtree->leafcard = MAXCARD;
    /* NOTE: min fill can be changed if needed. */
    new_rtree->min_node_fill = (new_rtree->nodecard - 1) / 2;
    new_rtree->min_leaf_fill = (new_rtree->leafcard - 1) / 2;

    n = RTreeNewNode(new_rtree, 0);
    new_rtree->n_levels = n->level = 0;	/* leaf */
    new_rtree->root = n;

    new_rtree->n_nodes = 1;
    new_rtree->n_leafs = 0;

    return new_rtree;
}

void RTreeFreeIndex(struct RTree *t)
{
    assert(t);

    if (t->root)
	RTreeDestroyNode(t->root, t->nodecard);

    free(t);
}

/*
 * Search in an index tree for all data retangles that
 * overlap the argument rectangle.
 * Return the number of qualifying data rects.
 */
int RTreeSearch(struct RTree *t, struct Rect *r, SearchHitCallback shcb,
		void *cbarg)
{
    struct Node *n;
    int hitCount = 0, found;
    int i;
    struct stack s[MAXLEVEL];
    int top = 0;

    assert(r);
    assert(t);

    /* stack size of t->n_levels + 1 is enough because of depth first search */
    /* only one node per level on stack at any given time */

    /* add root node position to stack */
    s[top].sn = t->root;
    s[top].branch_id = i = 0;
    n = s[top].sn;

    while (top >= 0) {
	n = s[top].sn;
	if (s[top].sn->level > 0) {	/* this is an internal node in the tree */
	    found = 1;
	    for (i = s[top].branch_id; i < t->nodecard; i++) {
		if (s[top].sn->branch[i].child.ptr &&
		    RTreeOverlap(r, &(s[top].sn->branch[i].rect), t)) {
		    s[top++].branch_id = i + 1;
		    /* add next node to stack */
		    s[top].sn = n->branch[i].child.ptr;
		    s[top].branch_id = 0;
		    found = 0;
		    break;
		}
	    }
	    if (found) {
		/* nothing else found, go back up */
		s[top].branch_id = t->nodecard;
		top--;
	    }
	}
	else {			/* this is a leaf node */
	    for (i = 0; i < t->leafcard; i++) {
		if (s[top].sn->branch[i].child.id &&
		    RTreeOverlap(r, &(s[top].sn->branch[i].rect), t)) {
		    hitCount++;
		    if (shcb) {	/* call the user-provided callback */
			if (!shcb(s[top].sn->branch[i].child.id, cbarg)) {
			    /* callback wants to terminate search early */
			    return hitCount;
			}
		    }
		}
	    }
	    top--;
	}
    }

    return hitCount;
}

/* 
 * Free ListBranch
 */
static void RTreeFreeListBranch(struct ListBranch *p)
{
    free(p);
}

/*
 * Inserts a new data rectangle into the index structure.
 * Non-recursively descends tree.
 * Returns 0 if node was not split and nothing was removed.
 * Returns 1 if root node was split. Old node updated to become one of two.
 * Returns 2 if branches need to be reinserted.  
 * The level argument specifies the number of steps up from the leaf
 * level to insert; e.g. a data rectangle goes in at level = 0.
 */
static int RTreeInsertRect2(struct Rect *r, union Child child, int level,
			    struct Node **newnode, struct RTree *t,
			    struct ListBranch **ee, int *overflow)
{
    int i;
    struct Branch b;
    struct Node *n, *n2;
    struct Rect *cover;
    struct stack s[MAXLEVEL];
    int top = 0, down = 0;
    int result;

    assert(r && newnode && t);

    /* add root node to stack */
    s[top].sn = t->root;

    /* go down to level of insertion */
    while (s[top].sn->level > level) {
	n = s[top].sn;
	i = RTreePickBranch(r, n, t);
	s[top++].branch_id = i;
	/* add next node to stack */
	s[top].sn = n->branch[i].child.ptr;
    }

    /* Have reached level for insertion. Remove p rectangles or split */
    if (s[top].sn->level == level) {
	b.rect = *r;
	/* child field of leaves contains tid of data record */
	b.child = child;
	/* add branch, may split node or remove branches */
	cover = &(s[top - 1].sn->branch[s[top - 1].branch_id].rect);
	result = RTreeAddBranch(&b, s[top].sn, &n2, ee, cover, overflow, t);
	/* update node count */
	if (result == 1) {
	    t->n_nodes++;
	}
    }
    else {
	/* Not supposed to happen */
	assert(FALSE);
	return 0;
    }

    /* go back up */
    while (top) {
	down = top--;
	i = s[top].branch_id;
	if (result == 0) {	/* branch was added */
	    s[top].sn->branch[i].rect =
		RTreeCombineRect(r, &(s[top].sn->branch[i].rect), t);
	}
	else if (result == 2) {	/* branches were removed */
	    /* get node cover of previous node */
	    s[top].sn->branch[i].rect = RTreeNodeCover(s[down].sn, t);
	}
	else if (result == 1) {	/* node was split */
	    /* get node cover of previous node */
	    s[top].sn->branch[i].rect = RTreeNodeCover(s[down].sn, t);
	    /* add new branch for new node previously added by RTreeAddBranch() */
	    b.child.ptr = n2;
	    b.rect = RTreeNodeCover(b.child.ptr, t);

	    /* add branch, may split node or remove branches */
	    cover = &(s[top - 1].sn->branch[s[top - 1].branch_id].rect);
	    result =
		RTreeAddBranch(&b, s[top].sn, &n2, ee, cover, overflow, t);

	    /* update node count */
	    if (result == 1) {
		t->n_nodes++;
	    }
	}
    }

    *newnode = n2;

    return result;
}

/* 
 * Insert a data rectangle into an index structure.
 * RTreeInsertRect1 provides for splitting the root;
 * returns 1 if root was split, 0 if it was not.
 * The level argument specifies the number of steps up from the leaf
 * level to insert; e.g. a data rectangle goes in at level = 0.
 * RTreeInsertRect2 does the actual insertion.
 */
static int RTreeInsertRect1(struct Rect *r, union Child child, int level,
			    struct RTree *t)
{
    struct Node *newnode;
    struct Node *newroot;
    struct Branch b;
    struct ListBranch *reInsertList = NULL;
    struct ListBranch *e;
    int result;
    int i, overflow[MAXLEVEL];

    /* R*-tree forced reinsertion: for each level only once */
    for (i = 0; i < MAXLEVEL; i++)
	overflow[i] = 1;

    result =
	RTreeInsertRect2(r, child, level, &newnode, t, &reInsertList,
			 overflow);
			 
    if (result == 1) {		/* root split */
	/* grow a new root, & tree taller */
	t->n_levels++;
	newroot = RTreeNewNode(t, t->n_levels);
	newroot->level = t->n_levels;
	/* branch for old root */
	b.rect = RTreeNodeCover(t->root, t);
	b.child.ptr = t->root;
	RTreeAddBranch(&b, newroot, NULL, NULL, NULL, NULL, t);
	/* branch for new node created by RTreeInsertRect2() */
	b.rect = RTreeNodeCover(newnode, t);
	b.child.ptr = newnode;
	RTreeAddBranch(&b, newroot, NULL, NULL, NULL, NULL, t);
	/* set new root node */
	t->root = newroot;
	t->n_nodes++;
    }
    else if (result == 2) {	/* branches were removed */
	while (reInsertList) {
	    /* get next branch in list */
	    b = reInsertList->b;
	    level = reInsertList->level;
	    e = reInsertList;
	    reInsertList = reInsertList->next;
	    RTreeFreeListBranch(e);
	    /* reinsert branches */
	    result =
		RTreeInsertRect2(&(b.rect), b.child, level, &newnode, t,
				 &reInsertList, overflow);

	    if (result == 1) {	/* root split */
		/* grow a new root, & tree taller */
		t->n_levels++;
		newroot = RTreeNewNode(t, t->n_levels);
		newroot->level = t->n_levels;
		/* branch for old root */
		b.rect = RTreeNodeCover(t->root, t);
		b.child.ptr = t->root;
		RTreeAddBranch(&b, newroot, NULL, NULL, NULL, NULL, t);
		/* branch for new node created by RTreeInsertRect2() */
		b.rect = RTreeNodeCover(newnode, t);
		b.child.ptr = newnode;
		RTreeAddBranch(&b, newroot, NULL, NULL, NULL, NULL, t);
		/* set new root node */
		t->root = newroot;
		t->n_nodes++;
	    }
	}
    }

    return result;
}

/* 
 * Insert a data rectangle into an RTree index structure.
 * r pointer to rectangle
 * tid data id stored with rectangle, must be > 0
 * t RTree where rectangle should be inserted
 */
int RTreeInsertRect(struct Rect *r, int tid, struct RTree *t)
{
    union Child newchild;
    assert(r && t);

    t->n_leafs++;

    newchild.id = tid;

    return RTreeInsertRect1(r, newchild, 0, t);
}

/*
 * Allocate space for a node in the list used in DeletRect to
 * store Nodes that are too empty.
 */
static struct ListNode *RTreeNewListNode(void)
{
    return (struct ListNode *)malloc(sizeof(struct ListNode));
    /* return new ListNode; */
}

static void RTreeFreeListNode(struct ListNode *p)
{
    free(p);
}

/* 
 * Add a node to the reinsertion list.  All its branches will later
 * be reinserted into the index structure.
 */
static void RTreeReInsertNode(struct Node *n, struct ListNode **ee)
{
    register struct ListNode *l;

    l = RTreeNewListNode();
    l->node = n;
    l->next = *ee;
    *ee = l;
}

/*
 * Delete a rectangle from non-root part of an index structure.
 * Called by RTreeDeleteRect.  Descends tree non-recursively,
 * merges branches on the way back up.
 * Returns 1 if record not found, 0 if success.
 */
static int
RTreeDeleteRect2(struct Rect *r, union Child child, struct RTree *t,
		 struct ListNode **ee)
{
    int i, notfound = 1;
    struct Node *n;
    struct stack s[MAXLEVEL];
    int top = 0, down = 0;
    int minfill;

    assert(r && ee && t);

    /* add root node position to stack */
    s[top].sn = t->root;
    s[top].branch_id = 0;
    n = s[top].sn;

    while (notfound) {
	/* go down to level 0, remember path */
	if (s[top].sn->level > 0) {
	    n = s[top].sn;
	    for (i = s[top].branch_id; i < t->nodecard; i++) {
		if (n->branch[i].child.ptr &&
		    RTreeOverlap(r, &(n->branch[i].rect), t)) {
		    s[top++].branch_id = i + 1;
		    /* add next node to stack */
		    s[top].sn = n->branch[i].child.ptr;
		    s[top].branch_id = 0;

		    notfound = 0;
		    break;
		}
	    }
	    if (notfound) {
		/* nothing else found, go back up */
		s[top].branch_id = t->nodecard;
		top--;
	    }
	    else		/* found a way down but not yet the item */
		notfound = 1;
	}
	else {
	    for (i = 0; i < t->leafcard; i++) {
		if (s[top].sn->branch[i].child.id && s[top].sn->branch[i].child.id == child.id) {	/* found item */
		    RTreeDisconnectBranch(s[top].sn, i, t);
		    t->n_leafs--;
		    notfound = 0;
		    break;
		}
	    }
	    if (notfound)	/* continue searching */
		top--;
	}
    }

    if (notfound) {
	return notfound;
    }

    /* go back up */
    while (top) {
	down = top;
	top--;
	n = s[top].sn;
	i = s[top].branch_id - 1;
	assert(s[down].sn->level == s[top].sn->level - 1);

	minfill = (s[down].sn->level ? t->min_node_fill : t->min_leaf_fill);
	if (s[down].sn->count >= minfill) {
	    /* just update node cover */
	    s[top].sn->branch[i].rect = RTreeNodeCover(s[down].sn, t);
	}
	else {
	    /* not enough entries in child, eliminate child node */
	    RTreeReInsertNode(s[top].sn->branch[i].child.ptr, ee);
	    RTreeDisconnectBranch(s[top].sn, i, t);
	}
    }

    return notfound;
}

/*
 * should be called by RTreeDeleteRect() only
 * 
 * Delete a data rectangle from an index structure.
 * Pass in a pointer to a Rect, the tid of the record, ptr RTree.
 * Returns 1 if record not found, 0 if success.
 * RTreeDeleteRect1 provides for eliminating the root.
 */
static int RTreeDeleteRect1(struct Rect *r, union Child child,
			    struct RTree *t)
{
    int i, maxkids;
    struct Node *n;
    struct ListNode *reInsertList = NULL;
    struct ListNode *e;

    assert(r);
    assert(t);

    if (!RTreeDeleteRect2(r, child, t, &reInsertList)) {
	/* found and deleted a data item */

	/* reinsert any branches from eliminated nodes */
	while (reInsertList) {
	    t->n_nodes--;
	    n = reInsertList->node;
	    maxkids = (n->level > 0 ? t->nodecard : t->leafcard);
	    for (i = 0; i < maxkids; i++) {
		if (n->level > 0) {  /* reinsert node branches */
		    if (n->branch[i].child.ptr) {
			RTreeInsertRect1(&(n->branch[i].rect),
					 n->branch[i].child, n->level, t);
		    }
		}
		else {  /* reinsert leaf branches */
		    if (n->branch[i].child.id) {
			RTreeInsertRect1(&(n->branch[i].rect),
					 n->branch[i].child, n->level, t);
		    }
		}
	    }
	    e = reInsertList;
	    reInsertList = reInsertList->next;
	    RTreeFreeNode(e->node);
	    RTreeFreeListNode(e);
	}

	/* check for redundant root (not leaf, 1 child) and eliminate */
	n = t->root;

	if (n->count == 1 && n->level > 0) {
	    for (i = 0; i < t->nodecard; i++) {
		if (n->branch[i].child.ptr)
		    break;
	    }
	    t->root = n->branch[i].child.ptr;
	    RTreeFreeNode(n);
	}
	return 0;
    }
    else {
	return 1;
    }
}

/* 
 * Delete a data rectangle from an index structure.
 * Pass in a pointer to a Rect, the tid of the record, ptr RTree.
 * Returns 1 if record not found, 0 if success.
 * RTreeDeleteRect1 provides for eliminating the root.
 *
 * RTreeDeleteRect() should be called by external functions instead of 
 * RTreeDeleteRect1()
 * wrapper for RTreeDeleteRect1 not really needed, but restricts 
 * compile warnings to rtree lib
 * this way it's easier to fix if necessary? 
 */
int RTreeDeleteRect(struct Rect *r, int tid, struct RTree *t)
{
    union Child child;

    child.id = tid;
    
    return RTreeDeleteRect1(r, child, t);
}
